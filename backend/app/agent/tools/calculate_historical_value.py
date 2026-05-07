"""
Tool: calculate_historical_value
Answers: "If I had invested PKR X in fund Y, N years ago, what would it be worth today?"
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


def calculate_historical_value(
    fund_name: str,
    principal_pkr: float,
    years_ago: int,
) -> str:
    """
    Calculates what a past investment would be worth today using historical annualised returns.

    Args:
        fund_name: Name of the Alfalah fund.
        principal_pkr: The original investment amount in PKR.
        years_ago: How many years ago the investment was made.
    """
    matched_cat = next(
        (f for f in FUNDS if _normalize(f["name"]) == _normalize(fund_name)), None
    )
    fund_label = matched_cat["name"] if matched_cat else fund_name

    # Resolve annual return
    annual_return_pct: float | None = None
    if fund_label in STATIC_RETURNS:
        annual_return_pct = STATIC_RETURNS[fund_label]["annualized_return"]
    else:
        best_name, score = _best_match(fund_label, list(STATIC_RETURNS.keys()))
        if best_name and score >= 2:
            annual_return_pct = STATIC_RETURNS[best_name]["annualized_return"]
            fund_label = best_name

    if annual_return_pct is None:
        return (
            f"I don't have historical return data for **{fund_label}**. "
            f"Please contact Alfalah AMC for historical NAV data."
        )

    rate = annual_return_pct / 100.0
    current_value = principal_pkr * ((1 + rate) ** years_ago)
    total_gain = current_value - principal_pkr
    gain_pct = (total_gain / principal_pkr) * 100
    cagr_used = annual_return_pct

    return (
        f"📊 **Historical Value Calculation — {fund_label}**\n\n"
        f"• Original Investment ({years_ago} year{'s' if years_ago != 1 else ''} ago): **PKR {principal_pkr:,.0f}**\n"
        f"• Annualised Return Used: **{cagr_used:.1f}%** (historical average)\n\n"
        f"💰 **Estimated Current Value: PKR {current_value:,.0f}**\n"
        f"   Total Gain: PKR {total_gain:,.0f} ({gain_pct:.1f}% total return)\n\n"
        f"⚠️ _This is an estimate based on the fund's historical annualised return. "
        f"Actual returns compound based on real NAV movements which vary year to year. "
        f"Past performance is not indicative of future results._"
    )
