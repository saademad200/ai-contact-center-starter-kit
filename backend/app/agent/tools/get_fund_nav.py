"""
Tool: get_fund_nav
Fetches the latest NAV for an Alfalah fund.

Scrapes alfalahamc.com/nav-prices and parses the <select id="funds_nav"> dropdown,
which embeds all NAV data as data-* attributes on each <option>.
Falls back to static seeded data if the live scrape fails.
"""

from __future__ import annotations

import contextlib

import httpx
from bs4 import BeautifulSoup

from app.agent.tools.static_fund_data import STATIC_NAV


def _normalize(name: str) -> str:
    return name.lower().replace("&", "and").replace("-", " ").replace("  ", " ").strip()


def _best_match(target: str, candidates: list[str]) -> tuple[str | None, int]:
    """Word-overlap fuzzy match. Returns (best_name, score)."""
    target_words = set(_normalize(target).split())
    best, best_score = None, 0
    for c in candidates:
        score = len(target_words & set(_normalize(c).split()))
        if score > best_score:
            best, best_score = c, score
    return best, best_score


async def _scrape_alfalah_navs() -> dict[str, dict]:
    """
    Fetches alfalahamc.com/nav-prices and parses:
        <select id="funds_nav">
            <option data-nav="107.43" data-offer="..." data-validity="06 May 2026" ...>
                Alfalah GHP Money Market Fund
            </option>
        </select>
    Returns {fund_name: {nav, offer, date, return_monthly, return_since_inception}}
    """
    url = "https://www.alfalahamc.com/nav-prices"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AlfalahGPT/1.0)"}

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    select = soup.find("select", {"id": "funds_nav"})
    if not select:
        raise ValueError("funds_nav select not found on page")

    result: dict[str, dict] = {}
    for option in select.find_all("option"):
        name = option.get_text(strip=True)
        if not name:
            continue
        with contextlib.suppress(ValueError, TypeError):
            result[name] = {
                "nav": float(option.get("data-nav", 0)),
                "offer": float(option.get("data-offer", 0)),
                "date": option.get("data-validity", ""),
                "return_monthly": float(option.get("data-return", 0)),
                "return_since_inception": float(option.get("data-return_since_inspection", 0)),
            }

    return result


async def get_fund_nav(fund_name: str) -> str:
    """
    Fetches the latest Net Asset Value (NAV / unit price) for an Alfalah mutual fund.
    """
    # Try live scrape first
    live_data: dict[str, dict] = {}
    source_label = "alfalahamc.com (live)"
    with contextlib.suppress(Exception):
        live_data = await _scrape_alfalah_navs()

    nav_dict = live_data if live_data else STATIC_NAV
    if not live_data:
        source_label = "cached data (alfalahamc.com temporarily unavailable)"

    # Exact match first
    if fund_name in nav_dict:
        entry = nav_dict[fund_name]
        nav = entry.get("nav", "N/A")
        offer = entry.get("offer", 0)
        date = entry.get("date", "latest")
        ret_m = entry.get("return_monthly", None)
        ret_i = entry.get("return_since_inception", None)
        extras = []
        if ret_m is not None:
            extras.append(f"  • Monthly Return: **{ret_m:.4f}%**")
        if ret_i is not None:
            extras.append(f"  • Return Since Inception: **{ret_i:.4f}%**")
        extras_str = "\n" + "\n".join(extras) if extras else ""
        return (
            f"**{fund_name}**\n"
            f"  • NAV (Redemption Price): **PKR {nav:,.4f}**\n"
            f"  • Offer Price: PKR {offer:,.4f}\n"
            f"  • As of: {date}"
            f"{extras_str}\n\n"
            f"_Source: {source_label}_"
        )

    # Fuzzy match
    best_name, score = _best_match(fund_name, list(nav_dict.keys()))
    if best_name and score >= 2:
        entry = nav_dict[best_name]
        nav = entry.get("nav", "N/A")
        offer = entry.get("offer", 0)
        date = entry.get("date", "latest")
        ret_m = entry.get("return_monthly", None)
        ret_i = entry.get("return_since_inception", None)
        extras = []
        if ret_m is not None:
            extras.append(f"  • Monthly Return: **{ret_m:.4f}%**")
        if ret_i is not None:
            extras.append(f"  • Return Since Inception: **{ret_i:.4f}%**")
        extras_str = "\n" + "\n".join(extras) if extras else ""
        return (
            f"**{best_name}**\n"
            f"  • NAV (Redemption Price): **PKR {nav:,.4f}**\n"
            f"  • Offer Price: PKR {offer:,.4f}\n"
            f"  • As of: {date}"
            f"{extras_str}\n\n"
            f"_Source: {source_label}_"
        )

    return (
        f"I couldn't find the NAV for **{fund_name}**.\n\n"
        f"Please check the full list at: https://www.alfalahamc.com/nav-prices"
    )
