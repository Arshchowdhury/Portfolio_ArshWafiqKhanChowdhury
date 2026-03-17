"""
config.py — Apex Query Assistant
Environment configuration loader.

Supports two modes:
  - Local development: reads from .env file
  - Azure deployment: reads from Key Vault via Managed Identity

No credentials are hardcoded. All sensitive values come from
Key Vault (production) or .env (local dev only, never committed).

Author: Arsh Wafiq Khan Chowdhury
"""

import os
from dataclasses import dataclass
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv


@dataclass
class Config:
    # Azure OpenAI
    openai_endpoint: str
    openai_deployment: str
    openai_embedding_deployment: str
    openai_api_version: str

    # Azure AI Search
    search_endpoint: str
    search_index_name: str

    # Azure Blob Storage
    storage_account_name: str
    storage_container_name: str

    # Pipeline settings
    chunk_size_tokens: int = 512        # Target chunk size in tokens
    chunk_overlap_tokens: int = 64      # Overlap between chunks for context continuity
    top_k_results: int = 5              # Number of chunks retrieved per query
    min_score_threshold: float = 0.75   # Minimum cosine similarity for retrieval


def load_config(use_key_vault: bool = False, key_vault_url: str = None) -> Config:
    """
    Load configuration from environment or Key Vault.

    Args:
        use_key_vault: If True, fetch secrets from Azure Key Vault.
                       Used in production deployments.
        key_vault_url: Key Vault URI (required if use_key_vault=True)

    Returns:
        Config dataclass with all settings populated.

    Design decision: DefaultAzureCredential tries multiple auth methods
    in order: environment variables, Managed Identity, Azure CLI, VS Code.
    This means the same code works locally (Azure CLI) and in production
    (Managed Identity) without any code changes.
    """

    if use_key_vault and key_vault_url:
        return _load_from_key_vault(key_vault_url)

    # Local development: load from .env
    load_dotenv()
    return _load_from_env()


def _load_from_env() -> Config:
    """Load config from environment variables (.env for local dev)."""

    required = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_INDEX_NAME",
        "AZURE_STORAGE_ACCOUNT_NAME",
        "AZURE_STORAGE_CONTAINER_NAME",
    ]

    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in your values."
        )

    return Config(
        openai_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        openai_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        openai_embedding_deployment=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        search_endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        search_index_name=os.environ["AZURE_SEARCH_INDEX_NAME"],
        storage_account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"],
        storage_container_name=os.environ["AZURE_STORAGE_CONTAINER_NAME"],
        chunk_size_tokens=int(os.getenv("CHUNK_SIZE_TOKENS", "512")),
        chunk_overlap_tokens=int(os.getenv("CHUNK_OVERLAP_TOKENS", "64")),
        top_k_results=int(os.getenv("TOP_K_RESULTS", "5")),
        min_score_threshold=float(os.getenv("MIN_SCORE_THRESHOLD", "0.75")),
    )


def _load_from_key_vault(key_vault_url: str) -> Config:
    """
    Load config from Azure Key Vault using Managed Identity.
    Used in production — no secrets in environment variables.
    """

    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=key_vault_url, credential=credential)

    def get_secret(name: str) -> str:
        return client.get_secret(name).value

    return Config(
        openai_endpoint=get_secret("apex-openai-endpoint"),
        openai_deployment=get_secret("apex-openai-deployment"),
        openai_embedding_deployment=get_secret("apex-openai-embedding-deployment"),
        openai_api_version="2024-08-01-preview",
        search_endpoint=get_secret("apex-search-endpoint"),
        search_index_name=get_secret("apex-search-index-name"),
        storage_account_name=get_secret("apex-storage-account-name"),
        storage_container_name=get_secret("apex-storage-container-name"),
    )
