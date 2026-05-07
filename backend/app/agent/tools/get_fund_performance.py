"""
Tool: get_fund_performance
Returns performance figures for an Alfalah fund.
Uses monthly return and return-since-inception from the live NAV page,
and approximate annualised rates from static_fund_data for projection use.
"""

from __future__ import annotations

from app.agent.tools.get_fund_nav import _best_match, _scrape_alfalah_navs
from app.agent.tools.static_fund_data import STATIC_NAV, STATIC_RETURNS


async def get_fund_performance(fund_name: str) -> str:
    """
    Returns the latest performance returns for an Alfalah mutual fund.
    Includes monthly return, return since inception, and approximate annualised returns.
    """
    # Try live data first
    live_data: dict[str, dict] = {}
    source_label = "alfalahamc.com (live)"
    try:
        live_data = await _scrape_alfalah_navs()
    except Exception:
        pass

    nav_dict = live_data if live_data else STATIC_NAV
    if not live_data:
        source_label = "cached data"

    # Find fund in NAV data
    fund_label = fund_name
    nav_entry: dict | None = None
    if fund_name in nav_dict:
        nav_entry = nav_dict[fund_name]
        fund_label = fund_name
    else:
        best_name, score = _best_match(fund_name, list(nav_dict.keys()))
        if best_name and score >= 2:
            nav_entry = nav_dict[best_name]
            fund_label = best_name

    # Find in returns data for annualised figures
    returns_entry: dict | None = None
    if fund_label in STATIC_RETURNS:
        returns_entry = STATIC_RETURNS[fund_label]
    else:
        best_r, score_r = _best_match(fund_label, list(STATIC_RETURNS.keys()))
        if best_r and score_r >= 2:
            returns_entry = STATIC_RETURNS[best_r]

    if not nav_entry and not returns_entry:
        return f"I don't have performance data for **{fund_name}**.\n\nCheck: https://www.alfalahamc.com/nav-prices"

    lines = [f"**{fund_label}** — Performance Summary:\n"]

    if nav_entry:
        ret_m = nav_entry.get("return_monthly")
        ret_i = nav_entry.get("return_since_inception")
        if ret_m is not None:
            lines.append(f"  • Monthly Return:          **{ret_m:.4f}%**")
        if ret_i is not None:
            lines.append(f"  • Return Since Inception:  **{ret_i:.4f}%**")

    if returns_entry:
        lines.append("")
        if returns_entry.get("1y"):
            lines.append(f"  • ~1 Year Annualised:  **{returns_entry['1y']:.2f}%**")
        if returns_entry.get("3y"):
            lines.append(f"  • ~3 Year Annualised:  **{returns_entry['3y']:.2f}%**")
        if returns_entry.get("5y"):
            lines.append(f"  • ~5 Year Annualised:  **{returns_entry['5y']:.2f}%**")

    lines.append(f"\n⚠️ _Past performance is not indicative of future results._\n_Source: {source_label} | Alfalah AMC_")
    return "\n".join(lines)
