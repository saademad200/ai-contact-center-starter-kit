"""
Alfalah Fund Catalogue
=======================
Static authoritative list of all Alfalah AMC mutual funds with metadata.
This is the ground truth used by tools that list, filter, or recommend funds.
"""

from __future__ import annotations

FUNDS: list[dict] = [
    # ── Money Market ─────────────────────────────────────────────────────────
    {
        "name": "Alfalah GHP Money Market Fund",
        "category": "Money Market",
        "shariah": False,
        "risk": "low",
        "horizon": "short",
        "goal": ["income", "parking"],
        "description": (
            "Invests in short-term government securities, T-bills, and bank deposits. "
            "Ideal for parking surplus cash with daily liquidity and capital preservation."
        ),
    },
    {
        "name": "Alfalah GHP Islamic Money Market Fund",
        "category": "Islamic Money Market",
        "shariah": True,
        "risk": "low",
        "horizon": "short",
        "goal": ["income", "parking"],
        "description": (
            "Shariah-compliant money market fund investing in Islamic bank deposits, "
            "Sukuk, and short-term Islamic income instruments."
        ),
    },
    # ── Income ───────────────────────────────────────────────────────────────
    {
        "name": "Alfalah GHP Income Fund",
        "category": "Income",
        "shariah": False,
        "risk": "low",
        "horizon": "short-medium",
        "goal": ["income", "regular_income"],
        "description": (
            "Focuses on government securities, TFCs, and bank placements to deliver "
            "steady monthly income. Suitable for conservative investors seeking regular payouts."
        ),
    },
    {
        "name": "Alfalah GHP Islamic Income Fund",
        "category": "Islamic Income",
        "shariah": True,
        "risk": "low",
        "horizon": "short-medium",
        "goal": ["income", "regular_income"],
        "description": (
            "Shariah-compliant income fund investing in Sukuk, Islamic TFCs, and "
            "government Islamic securities for regular halal income."
        ),
    },
    {
        "name": "Alfalah Stable Return Fund",
        "category": "Income",
        "shariah": False,
        "risk": "low",
        "horizon": "short-medium",
        "goal": ["income", "capital_preservation"],
        "description": (
            "Targets stable, predictable returns through fixed-income instruments "
            "with minimal volatility — suited for retirees and risk-averse investors."
        ),
    },
    # ── Balanced ─────────────────────────────────────────────────────────────
    {
        "name": "Alfalah GHP Alpha Fund",
        "category": "Asset Allocation",
        "shariah": False,
        "risk": "medium",
        "horizon": "medium",
        "goal": ["growth", "wealth_building"],
        "description": (
            "Dynamically allocates between equities and fixed income to capture "
            "upside in rising markets while limiting downside in corrections."
        ),
    },
    {
        "name": "Alfalah GHP Value Fund",
        "category": "Asset Allocation",
        "shariah": False,
        "risk": "medium",
        "horizon": "medium",
        "goal": ["growth", "wealth_building"],
        "description": (
            "Value-oriented balanced fund that selects undervalued stocks combined "
            "with income instruments for long-term capital appreciation."
        ),
    },
    {
        "name": "Alfalah GHP Islamic Balanced Allocation Fund",
        "category": "Islamic Asset Allocation",
        "shariah": True,
        "risk": "medium",
        "horizon": "medium",
        "goal": ["growth", "wealth_building"],
        "description": (
            "Shariah-compliant balanced fund investing in Islamic equities and Sukuk "
            "for moderate growth with income components."
        ),
    },
    # ── Equity ───────────────────────────────────────────────────────────────
    {
        "name": "Alfalah GHP Stock Fund",
        "category": "Equity",
        "shariah": False,
        "risk": "high",
        "horizon": "long",
        "goal": ["growth", "wealth_building", "retirement"],
        "description": (
            "Actively managed equity fund investing primarily in PSX-listed blue-chip "
            "and growth stocks for long-term capital appreciation."
        ),
    },
    {
        "name": "Alfalah GHP Islamic Stock Fund",
        "category": "Islamic Equity",
        "shariah": True,
        "risk": "high",
        "horizon": "long",
        "goal": ["growth", "wealth_building", "retirement"],
        "description": (
            "Shariah-screened equity fund investing in KMI-30 and broader Islamic "
            "equity universe for high long-term growth potential."
        ),
    },
    {
        "name": "Alfalah GHP Consumer Index ETF",
        "category": "ETF",
        "shariah": False,
        "risk": "high",
        "horizon": "long",
        "goal": ["growth", "wealth_building"],
        "description": (
            "Exchange-Traded Fund tracking Pakistan's consumer sector index, "
            "offering low-cost passive equity exposure."
        ),
    },
    # ── Retirement ────────────────────────────────────────────────────────────
    {
        "name": "Alfalah GHP Pension Fund - Equity Sub-Fund",
        "category": "Voluntary Pension",
        "shariah": False,
        "risk": "high",
        "horizon": "long",
        "goal": ["retirement"],
        "description": (
            "Equity component of the voluntary pension scheme, targeting maximum "
            "long-term growth for retirement savings."
        ),
    },
    {
        "name": "Alfalah GHP Pension Fund - Debt Sub-Fund",
        "category": "Voluntary Pension",
        "shariah": False,
        "risk": "low",
        "horizon": "long",
        "goal": ["retirement", "income"],
        "description": (
            "Debt component of the voluntary pension scheme investing in "
            "government and corporate bonds for stable retirement income."
        ),
    },
    {
        "name": "Alfalah GHP Islamic Pension Fund - Equity Sub-Fund",
        "category": "Islamic Voluntary Pension",
        "shariah": True,
        "risk": "high",
        "horizon": "long",
        "goal": ["retirement"],
        "description": (
            "Shariah-compliant equity pension sub-fund for long-term halal retirement savings."
        ),
    },
    {
        "name": "Alfalah GHP Islamic Pension Fund - Debt Sub-Fund",
        "category": "Islamic Voluntary Pension",
        "shariah": True,
        "risk": "low",
        "horizon": "long",
        "goal": ["retirement", "income"],
        "description": (
            "Shariah-compliant debt pension sub-fund investing in Sukuk and Islamic "
            "income instruments for stable retirement income."
        ),
    },
]

RISK_LABELS = {"low": "Low Risk", "medium": "Medium Risk", "high": "High Risk"}
HORIZON_LABELS = {
    "short": "Short-term (< 1 year)",
    "short-medium": "Short to Medium-term (1–3 years)",
    "medium": "Medium-term (3–5 years)",
    "long": "Long-term (5+ years)",
}
GOAL_LABELS = {
    "income": "Regular Income",
    "parking": "Cash Parking / Liquidity",
    "regular_income": "Monthly Income (bills, groceries, school fees)",
    "capital_preservation": "Capital Preservation",
    "growth": "Capital Growth",
    "wealth_building": "Wealth Building",
    "retirement": "Retirement Planning",
}
