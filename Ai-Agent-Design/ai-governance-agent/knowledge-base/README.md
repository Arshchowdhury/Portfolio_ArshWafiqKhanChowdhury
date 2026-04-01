# Knowledge Base

This directory contains the governance documents indexed into Azure AI Search.
The RAG pipeline processes PDF and DOCX files only — all other formats are ignored.

> **Note:** No documents are committed to this repository.
> Source documents are either publicly available (links below) or internal to the
> organisation deploying this system.  Download or create your own copies and place
> them in this directory before running the indexer.

---

## Recommended Public Documents

The following publicly available documents represent the core AI governance
regulatory and framework landscape as of early 2026.  They are well-suited as a
starting knowledge base for testing the pipeline.

### EU AI Act (2024)
| Document | Source | Format |
|---|---|---|
| EU AI Act — Full Text (Regulation 2024/1689) | [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689) | PDF |
| EU AI Act — Summary Factsheet | [European Commission](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai) | PDF |

Save as: `EU_AI_Act_2024.pdf`

### NIST AI Risk Management Framework (AI RMF 1.0)
| Document | Source | Format |
|---|---|---|
| NIST AI RMF 1.0 | [NIST](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf) | PDF |
| NIST AI RMF Playbook | [NIST](https://airc.nist.gov/Docs/2) | PDF |

Save as: `NIST_AI_RMF_1.0.pdf`, `NIST_AI_RMF_Playbook.pdf`

### ISO/IEC 42001:2023 — AI Management Systems
| Document | Source | Format |
|---|---|---|
| ISO/IEC 42001 Overview | [ISO](https://www.iso.org/standard/81230.html) | PDF (purchase required) |
| Free summary/overview papers | Various academic sources | PDF |

Save as: `ISO_42001_AI_Management_Overview.pdf`

### Australian AI Governance
| Document | Source | Format |
|---|---|---|
| Australia's AI Ethics Framework | [DISR](https://www.industry.gov.au/publications/australias-artificial-intelligence-ethics-framework) | PDF |
| Voluntary AI Safety Standard (2024) | [DISR](https://www.industry.gov.au/publications/voluntary-ai-safety-standard) | PDF |
| Safe and Responsible AI in Australia — Consultation | [Attorney-General's](https://www.ag.gov.au/rights-and-protections/publications/safe-and-responsible-ai-in-australia) | PDF |

Save as: `Australia_AI_Ethics_Framework.pdf`, `Australia_Voluntary_AI_Safety_Standard.pdf`

### Microsoft Responsible AI
| Document | Source | Format |
|---|---|---|
| Microsoft Responsible AI Standard v2 | [Microsoft](https://blogs.microsoft.com/wp-content/uploads/prod/sites/5/2022/06/Microsoft-Responsible-AI-Standard-v2-General-Requirements-3.pdf) | PDF |
| Microsoft AI Critique Framework (2025) | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/system-message) | Web → PDF |

Save as: `Microsoft_Responsible_AI_Standard_v2.pdf`

---

## Internal Policy Templates

For a complete deployment, supplement the public documents with organisation-specific
governance artefacts:

- **AI Use Policy** — Acceptable use, prohibited applications, employee responsibilities
- **AI Procurement Checklist** — Vendor due diligence requirements for third-party AI
- **AI Incident Response Playbook** — Escalation paths, SLAs, communication templates
- **Data Classification Policy** — What data types may be processed by AI systems
- **Model Risk Management Policy** — Validation, monitoring, and retirement requirements

These should be authored internally and placed in a subdirectory:

```
knowledge-base/
├── public/
│   ├── EU_AI_Act_2024.pdf
│   ├── NIST_AI_RMF_1.0.pdf
│   └── ...
└── internal/
    ├── AI_Use_Policy.docx
    ├── AI_Procurement_Checklist.docx
    └── ...
```

---

## Indexing

Once documents are in place, run the indexer:

```bash
# Preview what will be indexed (no upload)
python scripts/run_indexer.py --dry-run

# Index all documents
python scripts/run_indexer.py
```

Re-running the indexer on unchanged documents is safe — Azure AI Search's
`upload_documents` operation performs an upsert using the deterministic chunk ID
(`md5(source_path::chunk_index)`), so existing documents are overwritten rather
than duplicated.

---

## Chunk Statistics (approximate)

| Document | Est. pages | Est. chunks (512 tok, 20% overlap) |
|---|---|---|
| EU AI Act Full Text | ~144 | ~600 |
| NIST AI RMF 1.0 | ~64 | ~260 |
| NIST AI RMF Playbook | ~90 | ~370 |
| Australia AI Ethics Framework | ~16 | ~65 |
| Microsoft Responsible AI Standard v2 | ~30 | ~120 |

Total estimated: ~1,400 chunks across the recommended public corpus.
At the default `top_k=5`, queries will surface the five most relevant chunks
after hybrid search + semantic re-ranking.
