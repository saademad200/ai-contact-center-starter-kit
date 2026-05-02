"""
Alfalah Knowledge Base Seeder — Data Gathering
================================================
Downloads real PDFs from alfalahamc.com for RAG and scrapes FAQs for fine-tuning.

Pipeline:
  RAG:          PDFs → knowledge_base/docs/offering_documents/  → `make ingest`
  Fine-Tuning:  FAQs → knowledge_base/docs/faqs/               → Lambda JSONL processor

Usage:
    pip install httpx beautifulsoup4
    python knowledge_base/scripts/seed.py
"""
import asyncio
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

DOCS_DIR = Path("knowledge_base/docs")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AlfalahGPT-Seeder/1.0)"}

# ── RAG: Offering Documents (real URLs scraped from alfalahamc.com) ───────────
RAG_OFFERING_DOCS = [
    {
        "url": "https://alfalahamc.com/wp-content/uploads/2026/02/OD-Alfalah-Islamic-Asset-Allocation-Fund-SECP-Approved.pdf",
        "filename": "OD_Alfalah_Islamic_Asset_Allocation_Fund.pdf",
        "fund_name": "Alfalah Islamic Asset Allocation Fund",
    },
    {
        "url": "https://alfalahamc.com/wp-content/uploads/2026/02/Offering-Document-Alfalah-Islamic-Income-Growth-Fund-SECP-Approved.pdf",
        "filename": "OD_Alfalah_Islamic_Income_Growth_Fund.pdf",
        "fund_name": "Alfalah Islamic Income Growth Fund",
    },
    {
        "url": "https://alfalahamc.com/wp-content/uploads/2026/03/Consolidated-OD-AAAF-Updated-Upto-16th-SOD-dated-July-03-2025.pdf",
        "filename": "COD_Alfalah_Asset_Allocation_Fund.pdf",
        "fund_name": "Alfalah Asset Allocation Fund",
    },
    {
        "url": "https://alfalahamc.com/wp-content/uploads/2026/04/OD-Alfalah-Balochistan-Pension-Fund-SECP-Approved.pdf",
        "filename": "OD_Alfalah_Balochistan_Pension_Fund.pdf",
        "fund_name": "Alfalah Balochistan Pension Fund",
    },
    {
        "url": "https://alfalahamc.com/wp-content/uploads/2026/04/OD-Alfalah-Balochistan-Islamic-Pension-Fund-SECP-Approved.pdf",
        "filename": "OD_Alfalah_Balochistan_Islamic_Pension_Fund.pdf",
        "fund_name": "Alfalah Balochistan Islamic Pension Fund",
    },
    {
        "url": "https://alfalahamc.com/wp-content/uploads/afalah_downloads/Alfalah-Financial-Sector-Fund-FFSOF-Consolidated-Document-1.pdf",
        "filename": "COD_Alfalah_Financial_Sector_Opportunity_Fund.pdf",
        "fund_name": "Alfalah Financial Sector Opportunity Fund",
    },
    {
        "url": "https://alfalahamc.com/wp-content/uploads/afalah_downloads/Alfalah-Pension-Fund-II-Consolidated-Document-2.pdf",
        "filename": "COD_Alfalah_Pension_Fund_II.pdf",
        "fund_name": "Alfalah Pension Fund II",
    },
]

# ── Fine-Tuning: Web pages to scrape for FAQ text ────────────────────────────
SCRAPE_PAGES = [
    {
        "url": "https://alfalahamc.com/faqs/",
        "filename": "alfalah_faqs.txt",
        "description": "Alfalah AMC Official FAQs",
    },
    {
        "url": "https://alfalahamc.com/terms-conditions/",
        "filename": "alfalah_terms_conditions.txt",
        "description": "Terms & Conditions",
    },
    {
        "url": "https://alfalahamc.com/taxation/",
        "filename": "alfalah_taxation.txt",
        "description": "Taxation information for investors",
    },
    {
        "url": "https://alfalahamc.com/value-added-services/",
        "filename": "alfalah_value_added_services.txt",
        "description": "Value Added Services",
    },
]


async def download_pdf(client: httpx.AsyncClient, url: str, dest: Path) -> bool:
    if dest.exists():
        print(f"  [SKIP] {dest.name}")
        return True
    try:
        print(f"  [GET]  {dest.name} ...")
        r = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=60.0)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"  [OK]   {dest.name} ({len(r.content) // 1024} KB)")
        return True
    except Exception as e:
        print(f"  [ERR]  {dest.name}: {e}")
        return False


async def scrape_page(client: httpx.AsyncClient, url: str, dest: Path, description: str) -> None:
    if dest.exists():
        print(f"  [SKIP] {dest.name}")
        return
    try:
        print(f"  [GET]  {dest.name} — {description} ...")
        r = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=30.0)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Remove nav, header, footer, script, style noise
        for tag in soup(["nav", "header", "footer", "script", "style", "aside"]):
            tag.decompose()

        content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_="entry-content")
            or soup.find("div", id="content")
            or soup.body
        )
        text = content.get_text(separator="\n", strip=True) if content else soup.get_text()

        dest.write_text(text, encoding="utf-8")
        print(f"  [OK]   {dest.name} ({len(text):,} chars)")
    except Exception as e:
        print(f"  [ERR]  {dest.name}: {e}")


async def main() -> None:
    print("=" * 62)
    print("  Alfalah GPT — Knowledge Base Seeder")
    print("=" * 62)

    # ── Step 1: RAG — Download Offering Document PDFs ────────────
    rag_dir = DOCS_DIR / "offering_documents"
    rag_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[STEP 1] Downloading {len(RAG_OFFERING_DOCS)} Offering Documents for RAG...")

    async with httpx.AsyncClient() as client:
        for doc in RAG_OFFERING_DOCS:
            await download_pdf(client, doc["url"], rag_dir / doc["filename"])

        # ── Step 2: Fine-Tuning — Scrape FAQ & policy pages ──────
        ft_dir = DOCS_DIR / "faqs"
        ft_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[STEP 2] Scraping {len(SCRAPE_PAGES)} pages for Fine-Tuning seed data...")

        for page in SCRAPE_PAGES:
            await scrape_page(client, page["url"], ft_dir / page["filename"], page["description"])

    print("\n" + "=" * 62)
    print("  Done! Next steps:")
    print("    make ingest   → embeds PDFs into ChromaDB (RAG)")
    print("    Upload docs/faqs/*.txt via Admin Panel → S3 → Lambda")
    print("                    → cleaned JSONL → OpenAI Fine-Tuning")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(main())
