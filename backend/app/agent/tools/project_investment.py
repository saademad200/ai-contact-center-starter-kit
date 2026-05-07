"""
Tool: project_investment
Calculates the projected future value of an investment in an Alfalah fund.

Example: "If I invest PKR 500,000 in the Stock Fund today, what will it be worth in 5 years?"
"""

from __future__ import annotations

from app.agent.tools.fund_catalogue import FUNDS
from app.agent.tools.static_fund_data import STATIC_RETURNS


def _normalize(name: str) -> str:
    return name.lower().replace("-", " ").replace("  ", " ").strip()


def _best_match(target: str, candidates: list[str]) -> tuple[str | None, int]:
    target_words = set(_normalize(target).split())
    best, best_score = None, 0
    for c in candidates:
        score = len(target_words & set(_normalize(c).split()))
        if score > best_score:
            best, best_score = c, score
    return best, best_score


def project_investment(
    fund_name: str,
    principal_pkr: float,
    years: int,
    annual_return_pct: float | None = None,
) -> str:
    """
    Projects the future value of an investment using compound growth.

    Args:
        fund_name: Name of the Alfalah fund.
        principal_pkr: Initial investment amount in PKR.
        years: Number of years to project.
        annual_return_pct: Override the expected annual return % (optional).
                           If not provided, uses the fund's historical annualised return.
    """
    matched_cat = next((f for f in FUNDS if _normalize(f["name"]) == _normalize(fund_name)), None)
    fund_label = matched_cat["name"] if matched_cat else fund_name

    # Resolve annual return
    if annual_return_pct is None:
        if fund_label in STATIC_RETURNS:
            annual_return_pct = STATIC_RETURNS[fund_label]["annualized_return"]
        else:
            best_name, score = _best_match(fund_label, list(STATIC_RETURNS.keys()))
            if best_name and score >= 2:
                annual_return_pct = STATIC_RETURNS[best_name]["annualized_return"]
                fund_label = best_name
            else:
                return (
                    f"I don't have return data for **{fund_label}**. "
                    f"Please provide an expected annual return % to calculate the projection."
                )

    rate = annual_return_pct / 100.0
    future_value = principal_pkr * ((1 + rate) ** years)
    total_gain = future_value - principal_pkr
    gain_pct = (total_gain / principal_pkr) * 100

    # Year-by-year breakdown
    yearly_rows = []
    for y in range(1, min(years + 1, 11)):  # cap display at 10 years
        fv = principal_pkr * ((1 + rate) ** y)
        yearly_rows.append(f"  Year {y:>2}: PKR {fv:>13,.0f}")

    breakdown = "\n".join(yearly_rows)

    return (
        f"📈 **Investment Projection — {fund_label}**\n\n"
        f"• Initial Investment: **PKR {principal_pkr:,.0f}**\n"
        f"• Expected Annual Return: **{annual_return_pct:.1f}%** (based on historical performance)\n"
        f"• Projection Period: **{years} year{'s' if years != 1 else ''}**\n\n"
        f"💰 **Projected Value: PKR {future_value:,.0f}**\n"
        f"   Total Gain: PKR {total_gain:,.0f} ({gain_pct:.1f}%)\n\n"
        f"**Year-by-Year Breakdown:**\n{breakdown}\n\n"
        f"⚠️ _This is an illustrative projection based on past performance. "
        f"Actual returns may vary. Past performance is not indicative of future results. "
        f"Investments are subject to market risk._"
    )
