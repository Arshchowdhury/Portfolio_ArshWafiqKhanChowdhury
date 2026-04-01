"""
Audit logger: records every query and response to a local JSONL file,
and optionally ships the same record to a SharePoint List via the
Microsoft Graph API.

Each audit record captures:
  - session_id: groups related turns in a conversation
  - timestamp:  ISO-8601 UTC
  - query:      the user's raw question
  - response:   the generated answer (or escalation message)
  - confidence_band: High / Medium / Escalated
  - top_score:  raw reranker score of the best-matching chunk
  - escalated:  bool — True when no chunks met the confidence threshold
  - citations:  list of {title, source_url, chunk_index} dicts

SharePoint integration is intentionally optional.  The local JSONL file
is always written first, so audit records are never lost if the Graph
API call fails.  The caller receives a warning but the query pipeline
is not interrupted.

Environment variables required for SharePoint upload:
  SHAREPOINT_SITE_ID      — Graph API site ID
  SHAREPOINT_LIST_ID      — Target list ID
  AZURE_TENANT_ID         — Azure AD tenant
  AZURE_CLIENT_ID         — App registration client ID
  AZURE_CLIENT_SECRET     — App registration client secret
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

from config.settings import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_record(
    session_id: str,
    query: str,
    response: str,
    confidence_band: str,
    top_score: float,
    escalated: bool,
    citations: list[dict],
) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "query": query,
        "response": response,
        "confidence_band": confidence_band,
        "top_score": round(top_score, 4),
        "escalated": escalated,
        "citations": citations,
    }


def _write_local(record: dict) -> None:
    """Append a single record to the JSONL audit log on disk."""
    log_path = Path(settings.audit_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _get_graph_token() -> str | None:
    """
    Acquire an OAuth2 client-credentials token for the Microsoft Graph API.

    Returns None (with a logged warning) if any required credential is absent,
    so the caller can skip the SharePoint upload gracefully.
    """
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")

    if not all([tenant_id, client_id, client_secret]):
        return None

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }

    try:
        resp = requests.post(token_url, data=payload, timeout=10)
        resp.raise_for_status()
        return resp.json().get("access_token")
    except requests.RequestException as exc:
        logger.warning("Graph token acquisition failed: %s", exc)
        return None


def _upload_to_sharepoint(record: dict) -> bool:
    """
    POST the audit record to a SharePoint List via Microsoft Graph.

    SharePoint List columns are expected to match the record field names
    (case-insensitive matching is handled by Graph API):
      Title (maps to session_id), Query, Response, ConfidenceBand,
      TopScore, Escalated, Citations, Timestamp

    Returns True on success, False on any failure.
    """
    site_id = os.getenv("SHAREPOINT_SITE_ID")
    list_id = os.getenv("SHAREPOINT_LIST_ID")

    if not site_id or not list_id:
        return False

    token = _get_graph_token()
    if not token:
        return False

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{site_id}"
        f"/lists/{list_id}/items"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # SharePoint List item fields
    fields = {
        "Title": record["session_id"] or "anonymous",
        "Query": record["query"][:255],           # SharePoint single-line limit
        "Response": record["response"][:5000],    # Multi-line text field
        "ConfidenceBand": record["confidence_band"],
        "TopScore": str(record["top_score"]),
        "Escalated": str(record["escalated"]),
        "Citations": json.dumps(record["citations"])[:2000],
        "Timestamp": record["timestamp"],
    }

    try:
        resp = requests.post(
            url,
            headers=headers,
            json={"fields": fields},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.warning("SharePoint audit upload failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_query(
    session_id: str,
    query: str,
    response: str,
    confidence_band: str,
    top_score: float,
    escalated: bool,
    citations: list[dict],
) -> None:
    """
    Record an audit entry for a single query-response turn.

    Always writes to the local JSONL file first.  If SharePoint credentials
    are configured in environment variables, also attempts a Graph API upload.
    Failures in the SharePoint upload are logged as warnings and do not raise.

    Args:
        session_id:       Conversation session identifier.
        query:            The user's question.
        response:         The generated answer or escalation message.
        confidence_band:  "High", "Medium", or "Escalated".
        top_score:        Semantic reranker score of the best-matched chunk.
        escalated:        True if no chunks met the confidence threshold.
        citations:        List of citation dicts from the QueryResult.
    """
    record = _build_record(
        session_id=session_id,
        query=query,
        response=response,
        confidence_band=confidence_band,
        top_score=top_score,
        escalated=escalated,
        citations=citations,
    )

    # 1. Always write locally
    _write_local(record)

    # 2. Optionally ship to SharePoint
    uploaded = _upload_to_sharepoint(record)
    if not uploaded:
        logger.debug(
            "Audit record written locally only (SharePoint upload skipped or failed). "
            "session_id=%s",
            session_id,
        )
