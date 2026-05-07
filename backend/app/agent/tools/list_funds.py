"""
Tool: list_funds
Lists Alfalah mutual funds, optionally filtered by risk, horizon, goal, or Shariah compliance.
"""

from __future__ import annotations

from app.agent.tools.fund_catalogue import (
    FUNDS,
    HORIZON_LABELS,
    RISK_LABELS,
)


def list_funds(
    risk: str | None = None,
    horizon: str | None = None,
    goal: str | None = None,
    shariah_only: bool = False,
) -> str:
    """
    Returns a filtered list of Alfalah mutual funds.

    Args:
        risk: Filter by risk level — "low", "medium", or "high".
        horizon: Filter by investment horizon — "short", "short-medium", "medium", or "long".
        goal: Filter by investor goal — e.g. "income", "growth", "retirement", "regular_income".
        shariah_only: If True, only return Shariah-compliant funds.
    """
    results = FUNDS

    if shariah_only:
        results = [f for f in results if f["shariah"]]
    if risk:
        results = [f for f in results if f["risk"] == risk.lower()]
    if horizon:
        results = [f for f in results if f["horizon"] == horizon.lower()]
    if goal:
        results = [f for f in results if goal.lower() in f["goal"]]

    if not results:
        return "No funds matched your criteria. Please broaden your filters."

    lines = [f"Found {len(results)} fund(s) matching your criteria:\n"]
    for f in results:
        shariah_tag = " ✅ Shariah-Compliant" if f["shariah"] else ""
        lines.append(
            f"• **{f['name']}** [{f['category']}]{shariah_tag}\n"
            f"  Risk: {RISK_LABELS.get(f['risk'], f['risk'])} | "
            f"Horizon: {HORIZON_LABELS.get(f['horizon'], f['horizon'])}\n"
            f"  {f['description']}\n"
        )

    return "\n".join(lines)
