"""
Tool: recommend_funds
Recommends Alfalah mutual funds based on investor goal, risk appetite, and horizon.
"""

from __future__ import annotations

from app.agent.tools.fund_catalogue import FUNDS, GOAL_LABELS, HORIZON_LABELS, RISK_LABELS

GOAL_DESCRIPTIONS = {
    "regular_income": (
        "Funds that provide monthly complementary income to cater to regular expenses "
        "like utility bills, groceries, and school fees."
    ),
    "income": "Funds focused on delivering steady income with capital preservation.",
    "parking": "Short-term, highly liquid funds for parking surplus cash.",
    "capital_preservation": "Funds that prioritise protecting your capital from loss.",
    "growth": "Funds that target capital appreciation over the medium to long term.",
    "wealth_building": "Funds for building wealth through equity market participation.",
    "retirement": "Voluntary pension and long-term funds designed for retirement savings.",
}

RISK_GUIDANCE = {
    "low": (
        "Low-risk funds are perfect for investors seeking competitive returns while "
        "avoiding potential losses. These include money market, income, and sovereign funds."
    ),
    "medium": (
        "Medium-risk funds balance growth potential with income. Asset allocation and "
        "balanced funds fall in this category — suitable for 3–5 year horizons."
    ),
    "high": (
        "High-risk funds invest in equities and offer the greatest long-term return potential, "
        "but with higher short-term volatility. Suitable for 5+ year horizons."
    ),
}

HORIZON_GUIDANCE = {
    "short": (
        "Short-term funds invest in Islamic bank deposits, government securities, and "
        "short-term income instruments. Suitable for investors with a horizon under 1 year."
    ),
    "short-medium": (
        "Short to medium-term funds (1–3 years) invest in income instruments, Sukuk, and "
        "government securities offering medium to low risk."
    ),
    "medium": (
        "Medium-term funds (3–5 years) provide a balance of growth and income, "
        "suitable for investors who can tolerate moderate market fluctuations."
    ),
    "long": (
        "Long-term equity and pension funds (5+ years) are designed for wealth building "
        "and retirement. They offer the highest potential returns with higher short-term risk."
    ),
}


def recommend_funds(
    goal: str | None = None,
    risk: str | None = None,
    horizon: str | None = None,
    shariah_only: bool = False,
    max_results: int = 5,
) -> str:
    """
    Recommends Alfalah mutual funds tailored to the investor's goal, risk appetite,
    and investment horizon.

    Args:
        goal: Investor goal — "regular_income", "income", "parking", "capital_preservation",
              "growth", "wealth_building", or "retirement".
        risk: Risk appetite — "low", "medium", or "high".
        horizon: Investment horizon — "short", "short-medium", "medium", or "long".
        shariah_only: If True, only recommend Shariah-compliant funds.
        max_results: Maximum number of funds to recommend (default 5).
    """
    # Build context header
    header_parts = []
    if goal:
        desc = GOAL_DESCRIPTIONS.get(goal.lower(), "")
        if desc:
            header_parts.append(f"**Goal:** {GOAL_LABELS.get(goal.lower(), goal)}\n_{desc}_")
    if risk:
        guidance = RISK_GUIDANCE.get(risk.lower(), "")
        if guidance:
            header_parts.append(f"**Risk Appetite:** {RISK_LABELS.get(risk.lower(), risk)}\n_{guidance}_")
    if horizon:
        guidance = HORIZON_GUIDANCE.get(horizon.lower(), "")
        if guidance:
            header_parts.append(f"**Investment Horizon:** {HORIZON_LABELS.get(horizon.lower(), horizon)}\n_{guidance}_")

    # Filter funds
    results = FUNDS
    if shariah_only:
        results = [f for f in results if f["shariah"]]
    if risk:
        results = [f for f in results if f["risk"] == risk.lower()]
    if horizon:
        results = [f for f in results if f["horizon"] == horizon.lower()]
    if goal:
        results = [f for f in results if goal.lower() in f["goal"]]

    results = results[:max_results]

    header = "\n\n".join(header_parts)
    if not results:
        return (
            f"{header}\n\n"
            "No funds perfectly match all your criteria. "
            "I'd suggest broadening your risk or horizon preference, or speaking to an Alfalah AMC advisor."
        )

    lines = [f"{header}\n\n**Recommended Funds:**\n"] if header else ["**Recommended Funds:**\n"]
    for i, f in enumerate(results, 1):
        shariah_tag = " ✅ Shariah-Compliant" if f["shariah"] else ""
        lines.append(
            f"{i}. **{f['name']}** [{f['category']}]{shariah_tag}\n"
            f"   Risk: {RISK_LABELS.get(f['risk'], f['risk'])} | "
            f"Horizon: {HORIZON_LABELS.get(f['horizon'], f['horizon'])}\n"
            f"   {f['description']}\n"
        )

    lines.append("\n_To invest or learn more, visit https://www.alfalahamc.com or call 0800-ALFALAH (0800-253-2524)._")
    return "\n".join(lines)
