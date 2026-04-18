#!/usr/bin/env python3
"""
Knowledge Base Seed Script
==========================
Downloads publicly available documents for the KMS RAG pipeline:

Layer 1 — DOMAIN KNOWLEDGE:
    State Bank of Pakistan (SBP) regulatory documents
    (prudential regulations, AML/CFT, laws, forex framework)

Layer 2 — BANK APPLICATION KNOWLEDGE:
    HBL (Habib Bank Limited) public disclosures
    Pakistan's largest commercial bank — best public data coverage
    Source: hbl.com/assets/documents/ (direct, no auth required)

Usage:
    python knowledge_base/scripts/seed_knowledge_base.py
    python knowledge_base/scripts/seed_knowledge_base.py --category hbl
    python knowledge_base/scripts/seed_knowledge_base.py --category sbp
    python knowledge_base/scripts/seed_knowledge_base.py --dry-run
"""

import argparse
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
RAW_DOCS = ROOT / "knowledge_base" / "raw_docs"
METADATA_FILE = ROOT / "knowledge_base" / "metadata.json"

# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT CATALOGUE
# ─────────────────────────────────────────────────────────────────────────────
DOCUMENTS: list[dict] = [

    # =========================================================================
    # LAYER 1: SBP REGULATORY DOCUMENTS
    # Source: sbp.org.pk (Central Bank of Pakistan) — public domain
    # =========================================================================

    # ── Prudential Regulations ────────────────────────────────────────────────
    {
        "category": "sbp/prudential",
        "title": "Prudential Regulations for SME Financing (Jan 2025)",
        "url": "https://www.sbp.org.pk/publications/prudential/SME-PRs-Updtd-Jan-2025.pdf",
        "filename": "SBP_PR_SME_2025.pdf",
        "tags": ["sbp", "sme", "prudential", "financing", "regulation"],
        "description": (
            "SBP prudential regulations for SME financing. Covers eligibility, exposure "
            "limits, NPL classification, provisioning, and collateral requirements for "
            "SME loans — essential for banking software loan modules."
        ),
    },
    {
        "category": "sbp/prudential",
        "title": "Prudential Regulations for Consumer Financing",
        "url": "https://www.sbp.org.pk/publications/prudential/PRs-Consumer.pdf",
        "filename": "SBP_PR_Consumer.pdf",
        "tags": ["sbp", "consumer", "prudential", "credit-card", "auto-loan", "personal-loan"],
        "description": (
            "Consumer financing regulations covering personal loans, auto finance, "
            "credit cards, and housing finance. Debt burden ratio rules, exposure caps, "
            "credit assessment standards."
        ),
    },
    {
        "category": "sbp/prudential",
        "title": "Prudential Regulations for Microfinance Banks (2025)",
        "url": "https://www.sbp.org.pk/publications/prudential/PRs-Microfinance-Banks-2025.pdf",
        "filename": "SBP_PR_Microfinance_2025.pdf",
        "tags": ["sbp", "microfinance", "mfb", "prudential"],
        "description": (
            "Capital, liquidity, and lending requirements for microfinance banks "
            "regulated by SBP."
        ),
    },
    {
        "category": "sbp/prudential",
        "title": "Prudential Regulations for Agricultural Financing",
        "url": "https://www.sbp.org.pk/publications/prudential/PRsAgriApproved.pdf",
        "filename": "SBP_PR_Agriculture.pdf",
        "tags": ["sbp", "agriculture", "farming", "prudential"],
        "description": (
            "Agricultural lending framework including crop loan schemes, kisan "
            "credit card, repayment cycles aligned to harvest seasons."
        ),
    },
    {
        "category": "sbp/prudential",
        "title": "Prudential Regulations for Housing Finance",
        "url": "https://www.sbp.org.pk/smefd/2016/Housing-Finance-Prudential-Regulations.pdf",
        "filename": "SBP_PR_Housing.pdf",
        "tags": ["sbp", "housing", "mortgage", "prudential"],
        "description": "Housing and mortgage finance regulations including LTV ratios and income verification.",
    },

    # ── AML / CFT ─────────────────────────────────────────────────────────────
    {
        "category": "sbp/aml_cft",
        "title": "AML/CFT Risk-Based Approach Guidelines (2019)",
        "url": "https://www.sbp.org.pk/bprd/2019/C8-RBA-Guidelines.pdf",
        "filename": "SBP_AML_RBA_Guidelines.pdf",
        "tags": ["sbp", "aml", "cft", "kyc", "cdd", "fatf", "risk-based"],
        "description": (
            "Risk-based approach for AML/CFT. Covers CDD, EDD, STR, record keeping, "
            "high-risk customers, PEPs, and correspondent banking obligations."
        ),
    },
    {
        "category": "sbp/aml_cft",
        "title": "AML/CFT Sanctions Compliance (CL33 Annex B, 2022)",
        "url": "https://www.sbp.org.pk/bprd/2022/CL33-Annex-B.pdf",
        "filename": "SBP_AML_Sanctions_2022.pdf",
        "tags": ["sbp", "sanctions", "ofac", "un", "aml", "compliance"],
        "description": (
            "Sanctions screening obligations including OFAC SDN list, UN consolidated "
            "list, and SBP designated persons. Procedures for handling matches."
        ),
    },

    # ── Core Laws ─────────────────────────────────────────────────────────────
    {
        "category": "sbp/laws",
        "title": "State Bank of Pakistan Act, 1956",
        "url": "https://www.sbp.org.pk/about/act/SBP-Act.pdf",
        "filename": "SBP_Act_1956.pdf",
        "tags": ["sbp", "law", "central-bank", "legislation"],
        "description": (
            "Founding legislation of SBP. Defines its mandate, monetary policy authority, "
            "and supervisory jurisdiction over all banks in Pakistan."
        ),
    },
    {
        "category": "sbp/laws",
        "title": "Payment Systems and Electronic Fund Transfer Act, 2007",
        "url": "https://www.sbp.org.pk/psd/2007/EFT_Act_2007.pdf",
        "filename": "SBP_EFT_Act_2007.pdf",
        "tags": ["sbp", "payment", "eft", "rtgs", "digital", "legislation"],
        "description": (
            "Legal framework for RTGS, clearing houses, digital wallets, and electronic "
            "payment instruments. Critical for payment module architecture."
        ),
    },
    {
        "category": "sbp/laws",
        "title": "Credit Bureau Act, 2015",
        "url": "https://www.sbp.org.pk/about/act/CreditBureauAct-2015.pdf",
        "filename": "SBP_Credit_Bureau_Act_2015.pdf",
        "tags": ["sbp", "credit", "bureau", "ecib", "scoring"],
        "description": (
            "Governs credit bureaus in Pakistan (eCIB). Data sharing obligations, "
            "consumer rights, and credit report dispute resolution."
        ),
    },
    {
        "category": "sbp/laws",
        "title": "Electronic Transactions Ordinance, 2002",
        "url": "https://www.sbp.org.pk/about/act/ETC202.pdf",
        "filename": "SBP_Electronic_Transactions_2002.pdf",
        "tags": ["sbp", "digital", "e-signature", "electronic", "legislation"],
        "description": "Legal recognition of electronic signatures, digital contracts, and e-records in Pakistan.",
    },
    {
        "category": "sbp/laws",
        "title": "Financial Institutions (Recovery of Finances) Ordinance, 2001",
        "url": "https://www.sbp.org.pk/about/ordinance/Ordinance_1.pdf",
        "filename": "SBP_Recovery_Ordinance_2001.pdf",
        "tags": ["sbp", "npl", "recovery", "default", "legal"],
        "description": "Legal framework for NPL recovery via Banking Courts. Defines enforcement and rehabilitation procedures.",
    },

    # ── Forex ─────────────────────────────────────────────────────────────────
    {
        "category": "sbp/forex",
        "title": "Regulatory Framework for Exchange Companies",
        "url": "https://www.sbp.org.pk/epd/pdf/Regulatory-Framework-for-Exchange-Companies.pdf",
        "filename": "SBP_Exchange_Companies_Framework.pdf",
        "tags": ["sbp", "forex", "exchange", "remittance", "hawala"],
        "description": (
            "Licensing, capital requirements, and AML obligations for exchange companies. "
            "Relevant for multi-currency and remittance modules."
        ),
    },

    # =========================================================================
    # LAYER 2: HBL (HABIB BANK LIMITED) PUBLIC DISCLOSURES
    # Pakistan's largest commercial bank — best public data coverage
    # Source: hbl.com/assets/documents/ — verified direct links (no auth)
    # =========================================================================

    # ── HBL Annual Reports ────────────────────────────────────────────────────
    {
        "category": "hbl/annual_reports",
        "title": "HBL Annual Report 2024",
        "url": "https://www.hbl.com/assets/documents/HBL_Annual_Report_2024.pdf",
        "filename": "HBL_Annual_Report_2024.pdf",
        "tags": ["hbl", "annual-report", "financial-statements", "2024"],
        "description": (
            "HBL's full 2024 annual report. Contains audited financial statements, "
            "business segment performance (retail, corporate, Islamic), risk management "
            "framework, AML/compliance disclosures, and product portfolio overview. "
            "Excellent reference for understanding how a full-scale Pakistani commercial "
            "bank operates."
        ),
    },
    {
        "category": "hbl/annual_reports",
        "title": "HBL Annual Report 2023",
        "url": "https://www.hbl.com/assets/documents/HBL_Annual_Report_2023.pdf",
        "filename": "HBL_Annual_Report_2023.pdf",
        "tags": ["hbl", "annual-report", "financial-statements", "2023"],
        "description": (
            "HBL 2023 annual report. Covers digital transformation initiatives, "
            "HBL Mobile app, Konnect by HBL (branchless banking), loan portfolio "
            "quality, SBP regulatory compliance, and ESG reporting."
        ),
    },
    {
        "category": "hbl/annual_reports",
        "title": "HBL Annual Report 2022",
        "url": "https://www.hbl.com/assets/documents/HBL_Annual_Report_2022.pdf",
        "filename": "HBL_Annual_Report_2022.pdf",
        "tags": ["hbl", "annual-report", "financial-statements", "2022"],
        "description": (
            "HBL 2022 annual report including post-flood economic impact analysis, "
            "agriculture finance expansion, and Islamic banking (HBL Nisa, HBL Kisan)."
        ),
    },
    {
        "category": "hbl/annual_reports",
        "title": "HBL Annual Report 2021",
        "url": "https://www.hbl.com/assets/documents/HBL_Annual_Report_2021.pdf",
        "filename": "HBL_Annual_Report_2021.pdf",
        "tags": ["hbl", "annual-report", "financial-statements", "2021", "covid"],
        "description": (
            "Post-COVID recovery year: DLTL schemes, SBP refinancing facilities taken, "
            "Raast integration, and SME lending expansion."
        ),
    },

    # ── HBL Quarterly Reports ─────────────────────────────────────────────────
    {
        "category": "hbl/quarterly_reports",
        "title": "HBL Half-Yearly Report June 2024",
        "url": "https://www.hbl.com/assets/documents/HBL_Half_Yearly_Report_-_June_30%2C_2024.pdf",
        "filename": "HBL_HY_Report_June_2024.pdf",
        "tags": ["hbl", "quarterly", "half-yearly", "financial-statements", "2024"],
        "description": (
            "HBL H1 2024 financial results. Useful for understanding mid-year performance "
            "metrics, advances portfolio, deposit mix, and CASA ratio trends."
        ),
    },
    {
        "category": "hbl/quarterly_reports",
        "title": "HBL Quarterly Report Q1 2024 (March 31, 2024)",
        "url": "https://www.hbl.com/assets/documents/HBL_Quarterly_Report_March_31%2C_2024.pdf",
        "filename": "HBL_Q1_Report_March_2024.pdf",
        "tags": ["hbl", "quarterly", "financial-statements", "2024", "q1"],
        "description": (
            "Q1 2024 condensed interim financial statements. Key ratios: CAR, NPL coverage, "
            "ADR (Advance to Deposit Ratio), liquid asset holdings."
        ),
    },
    {
        "category": "hbl/quarterly_reports",
        "title": "HBL Quarterly Report Q3 2024 (September 30, 2024)",
        "url": "https://www.hbl.com/assets/documents/HBL_Quarterly_Report_September_30%2C_2024.pdf",
        "filename": "HBL_Q3_Report_Sep_2024.pdf",
        "tags": ["hbl", "quarterly", "financial-statements", "2024", "q3"],
        "description": "Q3 2024 financial results including 9-month performance and international operations.",
    },
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download_document(doc: dict, dest_dir: Path, timeout: int = 120) -> dict | None:
    """Download a single document with streaming. Returns metadata on success."""
    dest_path = dest_dir / doc["category"] / doc["filename"]
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists():
        size_mb = dest_path.stat().st_size / (1024 * 1024)
        log.info("SKIP (cached, %.1f MB): %s", size_mb, doc["filename"])
        return {**doc, "local_path": str(dest_path.relative_to(ROOT)), "sha256": sha256_file(dest_path), "status": "cached"}

    log.info("↓  %s", doc["title"])

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; KMS-Seeder/1.0; "
            "+https://github.com/your-org/kms)"
        )
    }

    try:
        with httpx.stream("GET", doc["url"], timeout=timeout, follow_redirects=True, headers=headers) as r:
            r.raise_for_status()
            downloaded = 0
            with open(dest_path, "wb") as f:
                for chunk in r.iter_bytes(chunk_size=16384):
                    f.write(chunk)
                    downloaded += len(chunk)

        size_mb = downloaded / (1024 * 1024)
        log.info("   ✓ %.1f MB → %s", size_mb, dest_path.relative_to(ROOT))
        return {
            **doc,
            "local_path": str(dest_path.relative_to(ROOT)),
            "sha256": sha256_file(dest_path),
            "size_bytes": downloaded,
            "status": "downloaded",
        }

    except httpx.HTTPStatusError as e:
        log.error("   ✗ HTTP %s — %s", e.response.status_code, doc["url"])
    except httpx.RequestError as e:
        log.error("   ✗ Network error — %s: %s", doc["url"], e)

    return None


def save_metadata(metadata: list[dict]) -> None:
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(
            {
                "version": "1.0",
                "layers": {
                    "sbp": "State Bank of Pakistan — regulatory documents (public domain)",
                    "hbl": "HBL (Habib Bank Limited) — public investor disclosures",
                },
                "documents": metadata,
            },
            f,
            indent=2,
        )
    log.info("Metadata → %s", METADATA_FILE.relative_to(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Download KMS banking knowledge base documents")
    parser.add_argument(
        "--category",
        choices=["sbp", "hbl", "all"],
        default="all",
        help="Layer to download: sbp (regulatory), hbl (bank docs), or all",
    )
    parser.add_argument("--dry-run", action="store_true", help="List docs without downloading")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between downloads")
    args = parser.parse_args()

    docs = [d for d in DOCUMENTS if args.category == "all" or d["category"].startswith(args.category)]

    log.info("━" * 60)
    log.info("KMS Knowledge Base Seeder")
    log.info("Layer 1 (SBP): %d regulatory docs", sum(1 for d in docs if d["category"].startswith("sbp")))
    log.info("Layer 2 (HBL): %d bank docs", sum(1 for d in docs if d["category"].startswith("hbl")))
    log.info("Total: %d documents", len(docs))
    log.info("━" * 60)

    if args.dry_run:
        for d in docs:
            log.info("[DRY-RUN] %s  ← %s", d["filename"], d["url"])
        return 0

    RAW_DOCS.mkdir(parents=True, exist_ok=True)
    metadata, success, failed = [], 0, 0

    for i, doc in enumerate(docs, 1):
        log.info("[%d/%d]", i, len(docs))
        result = download_document(doc, RAW_DOCS)
        if result:
            metadata.append(result)
            success += 1
        else:
            failed += 1
        if i < len(docs):
            time.sleep(args.delay)

    save_metadata(metadata)
    log.info("━" * 60)
    log.info("Done — %d succeeded, %d failed", success, failed)
    log.info("Raw docs saved to: %s", RAW_DOCS.relative_to(ROOT))
    log.info("━" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
