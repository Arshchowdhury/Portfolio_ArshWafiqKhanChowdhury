# Knowledge Base

This directory is the document source for the AI Governance Advisory Agent's RAG pipeline. It is intentionally empty in the repository.

---

## Why there are no PDFs here

The knowledge base is populated at deploy time, not committed to version control. Running `scripts/run_indexer.py` reads documents from this directory, chunks them, embeds them using the Azure OpenAI embeddings endpoint, and upserts the resulting vectors into the Azure AI Search index. The index — not the source files — is the production artefact.

Committing PDFs would bloat the repository, create a stale copy of documents that change over time, and potentially expose governance content that belongs in controlled internal systems. The correct place for source documents is a SharePoint document library or Azure Blob Storage container, which the indexer reads from at runtime.

---

## Recommended document corpus

The agent is designed around publicly available AI governance frameworks supplemented by organisation-specific internal policies.

**Public documents (suggested)**

| Document | Source | Notes |
|---|---|---|
| EU AI Act (2024) — full text and summary factsheet | Official Journal of the EU | Primary regulatory reference for EU-adjacent clients |
| NIST AI RMF 1.0 and Playbook | nist.gov | Risk categorisation and control mapping |
| ISO/IEC 42001:2023 — AI Management Systems overview | ISO | Certification pathway reference |
| Australian AI Ethics Framework | DISR | Mandatory for Australian government engagements |
| Australian Voluntary AI Safety Standard | DISR | 2024 update |
| Microsoft Responsible AI Standard v2 | Microsoft | Directly relevant to Copilot / Azure AI deployments |

**Internal documents (organisation-specific)**

These are not committed and must be sourced from the client's controlled environment:

- Acceptable use policy for AI tools
- AI procurement checklist
- Incident response and escalation procedures
- Data classification and handling guidelines
- Model risk management policy

---

## Directory structure

```
knowledge-base/
├── public/          # Public regulatory and framework documents
│   ├── eu-ai-act-summary.pdf
│   ├── nist-ai-rmf-1.0.pdf
│   └── ...
├── internal/        # Organisation-specific policies (not committed)
│   └── .gitkeep
└── README.md
```

The indexer processes all `.pdf` and `.docx` files recursively. Other formats are ignored.

---

## Indexing

```bash
# Dry run — list files that would be indexed without writing to Azure
python scripts/run_indexer.py --dry-run

# Full index run
python scripts/run_indexer.py
```

The indexer performs upsert operations so re-running on an unchanged corpus is safe. Approximate scale for the recommended public corpus: ~370 pages, ~1,400 chunks, returning the top 5 most relevant chunks per query via hybrid BM25 + vector search with semantic re-ranking.

---

## Governance note

In a production deployment, source documents should be versioned in SharePoint or Azure Blob Storage with access controls matching the agent's intended audience. The indexer should be triggered by a Power Automate flow or Azure Function on document change, not run manually. The current implementation is scoped for a prototype and consulting demonstration context.
