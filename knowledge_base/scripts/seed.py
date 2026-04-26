"""
Knowledge Base Seeder — See PROJECT_PLAN.md §4
================================================
Downloads Al Meezan fund docs, MUFAP data, and SECP regulations.

Verified sources:
- Al Meezan FMR: https://www.almeezangroup.com/assets/uploads/2026/02/FMR-February-2026.pdf
- Al Meezan fund prospectuses: almeezangroup.com → Downloads → Constitutive Documents
- MUFAP daily NAVs: https://www.mufap.com.pk/nav/scheme-value.php
- SECP mutual fund regulations: secp.gov.pk

Usage:
    pip install httpx beautifulsoup4
    python knowledge_base/scripts/seed.py
"""
