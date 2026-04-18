# Knowledge Base — Pakistan Banking Domain

This directory contains the **seed knowledge base** for the KMS RAG pipeline, built from publicly available State Bank of Pakistan (SBP) regulatory and legal documents.

---

## Why These Documents?

A **Pakistani banking-domain software company** needs its employees to understand:
- What regulations their banking clients must comply with
- How banking products (loans, payments, AML screening) work legally
- What SBP expects in terms of reporting and prudential limits

These documents answer those questions directly from the authoritative source.

---

## Document Categories

| Category | Documents | Use Case |
|----------|-----------|---------|
| **Prudential Regulations** | SME, Consumer, Housing, Microfinance, Agriculture | Loan product rules, exposure limits, provisioning |
| **AML/CFT** | Risk-Based Approach, Sanctions, FATF Framework | KYC/CDD workflows, sanctions screening, STR |
| **Core Laws** | SBP Act, Payment Systems Act, Credit Bureau Act, Electronic Transactions | Architecture decisions, compliance obligations |
| **Forex** | Exchange Companies Framework | Multi-currency, remittance modules |

---

## Document Catalogue (15 documents)

### Prudential Regulations
| File | Title | Year |
|------|-------|------|
| `PR_SME_Jan2025.pdf` | Prudential Regulations for SME Financing | 2025 |
| `PR_Consumer.pdf` | Prudential Regulations for Consumer Financing | Latest |
| `PR_Microfinance_2025.pdf` | Prudential Regulations for Microfinance Banks | 2025 |
| `PR_Housing_Finance.pdf` | Prudential Regulations for Housing Finance | 2016 |
| `PR_Agriculture.pdf` | Prudential Regulations for Agricultural Financing | Latest |

### AML / CFT
| File | Title | Year |
|------|-------|------|
| `AML_CFT_RBA_Guidelines.pdf` | Risk-Based Approach Guidelines | 2019 |
| `AML_CFT_Sanctions_CL33.pdf` | Sanctions Compliance (CL33 Annex B) | 2022 |
| `AML_FATF_Framework_CL20.pdf` | FATF Compliance Framework (CL20 Annex B) | 2017 |

### Core Laws
| File | Title | Year |
|------|-------|------|
| `SBP_Act_1956.pdf` | State Bank of Pakistan Act | 1956 |
| `Payment_Systems_EFT_Act_2007.pdf` | Payment Systems & EFT Act | 2007 |
| `Microfinance_Ordinance_2001.pdf` | Microfinance Institutions Ordinance | 2001 |
| `Credit_Bureau_Act_2015.pdf` | Credit Bureau Act | 2015 |
| `Electronic_Transactions_Ordinance_2002.pdf` | Electronic Transactions Ordinance | 2002 |
| `Recovery_of_Finances_Ordinance_2001.pdf` | Recovery of Finances Ordinance | 2001 |

### Forex
| File | Title | Year |
|------|-------|------|
| `Exchange_Companies_Framework.pdf` | Regulatory Framework for Exchange Companies | Latest |

---

## Setup & Download

```bash
# Install dependencies
pip install httpx

# Download all documents (~15 PDFs from sbp.org.pk)
python knowledge_base/scripts/seed_knowledge_base.py

# Download a specific category only
python knowledge_base/scripts/seed_knowledge_base.py --category prudential

# Preview what will be downloaded (no actual download)
python knowledge_base/scripts/seed_knowledge_base.py --dry-run
```

Documents are saved to `knowledge_base/raw_docs/<category>/`.

---

## Ingestion into the RAG Pipeline

Once downloaded, ingest via the API:

```bash
# Via the admin API endpoint
curl -X POST http://localhost:8000/api/v1/admin/ingest-all \
  -H "Authorization: Bearer <admin_token>"

# Or via the admin UI at http://localhost:3000/admin
# Upload individual PDFs via the drag-and-drop interface
```

The ingestion pipeline will:
1. Parse PDF text
2. Split into overlapping 512-token chunks
3. Generate embeddings via `sentence-transformers/all-MiniLM-L6-v2`
4. Store in ChromaDB `banking_knowledge` collection

---

## Source

All documents are from **[State Bank of Pakistan](https://www.sbp.org.pk)** — publicly accessible regulatory and legal publications. No proprietary or confidential information is included.
