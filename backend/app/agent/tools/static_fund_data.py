"""
Static NAV and returns data for Alfalah funds.
─────────────────────────────────────────────
Sourced directly from alfalahamc.com/nav-prices (HTML data-* attributes).
Used as fallback when live scraping fails.

Last updated: 06 May 2026
"""

# fmt: off
# Format: fund_name → {nav, offer, date, return_monthly, return_since_inception}
STATIC_NAV: dict[str, dict] = {
    "Alfalah GHP Money Market Fund": {
        "nav": 107.4362, "offer": 109.9072, "date": "06 May 2026",
        "return_monthly": 9.9791, "return_since_inception": 24.9575,
    },
    "Alfalah GHP Cash Fund": {
        "nav": 544.7849, "offer": 557.3150, "date": "06 May 2026",
        "return_monthly": 8.9717, "return_since_inception": 24.4896,
    },
    "Alfalah GHP Sovereign Fund": {
        "nav": 114.9071, "offer": 117.5500, "date": "06 May 2026",
        "return_monthly": 11.9428, "return_since_inception": 21.9614,
    },
    "Alfalah GHP Income Fund": {
        "nav": 123.7561, "offer": 126.6025, "date": "06 May 2026",
        "return_monthly": 9.3367, "return_since_inception": 30.0174,
    },
    "Alfalah GHP Income Multiplier Fund": {
        "nav": 63.0472, "offer": 65.2223, "date": "06 May 2026",
        "return_monthly": 10.5923, "return_since_inception": 20.1759,
    },
    "Alfalah Financial Sector Income Plan 1": {
        "nav": 109.1055, "offer": 111.6149, "date": "06 May 2026",
        "return_monthly": 10.1178, "return_since_inception": 18.3868,
    },
    "Alfalah GHP Alpha Fund": {
        "nav": 115.2400, "offer": 119.2158, "date": "06 May 2026",
        "return_monthly": 1.2181, "return_since_inception": 2030.5697,
    },
    "Alfalah GHP Stock Fund": {
        "nav": 199.8780, "offer": 205.6245, "date": "06 May 2026",
        "return_monthly": 1.2695, "return_since_inception": 2742.9823,
    },
    "Alfalah GHP Dedicated Equity Fund": {
        "nav": 208.8074, "offer": 213.6100, "date": "06 May 2026",
        "return_monthly": 1.1405, "return_since_inception": 302.8415,
    },
    "Alfalah GHP Value Fund": {
        "nav": 91.7399, "offer": 94.9049, "date": "06 May 2026",
        "return_monthly": 0.9909, "return_since_inception": 1405.0569,
    },
    "Alfalah Financial Value Plan 1": {
        "nav": 150.0935, "offer": 155.2717, "date": "06 May 2026",
        "return_monthly": 0.1903, "return_since_inception": 50.2824,
    },
    "Alfalah Consumer Index Exchange Traded Fund": {
        "nav": 17.1200, "offer": 17.1200, "date": "06 May 2026",
        "return_monthly": 0.7467, "return_since_inception": 61.9000,
    },
    "Alfalah Islamic Amdani Fund": {
        "nav": 101.1252, "offer": 103.4511, "date": "06 May 2026",
        "return_monthly": 7.7307, "return_since_inception": 17.1830,
    },
    "Alfalah Islamic Money Market Fund": {
        "nav": 108.8034, "offer": 111.3059, "date": "06 May 2026",
        "return_monthly": 8.5921, "return_since_inception": 17.1113,
    },
    "Alfalah GHP Islamic Income Fund": {
        "nav": 110.2658, "offer": 112.8019, "date": "06 May 2026",
        "return_monthly": 9.4900, "return_since_inception": 19.3461,
    },
    "Alfalah GHP Islamic Stock Fund": {
        "nav": 72.0547, "offer": 74.5406, "date": "06 May 2026",
        "return_monthly": 1.1860, "return_since_inception": 1170.0557,
    },
    "Alfalah GHP Islamic Dedicated Equity Fund": {
        "nav": 117.6551, "offer": 119.6847, "date": "06 May 2026",
        "return_monthly": 1.0782, "return_since_inception": 172.2680,
    },
    "Alfalah GHP Islamic Value Fund": {
        "nav": 139.6975, "offer": 142.9105, "date": "06 May 2026",
        "return_monthly": 0.1664, "return_since_inception": 93.2084,
    },
    "Alfalah GHP Pension Fund - Money Market": {
        "nav": 241.4136, "offer": 249.7424, "date": "05 Nov 2025",
        "return_monthly": 9.9736, "return_since_inception": 151.8306,
    },
    "Alfalah GHP Islamic Pension - Debt": {
        "nav": 213.4855, "offer": 220.8507, "date": "06 May 2026",
        "return_monthly": 9.8696, "return_since_inception": 108.7528,
    },
    "Alfalah GHP Islamic Pension - Equity": {
        "nav": 304.1404, "offer": 314.6332, "date": "05 Nov 2025",
        "return_monthly": -0.8713, "return_since_inception": 515.6428,
    },
    "Alfalah GHP Islamic Pension - Money Market": {
        "nav": 211.3396, "offer": 218.6308, "date": "05 Nov 2025",
        "return_monthly": 8.9608, "return_since_inception": 779.1035,
    },
    "Alfalah Government Securities Fund": {
        "nav": 135.2242, "offer": 138.3344, "date": "06 May 2026",
        "return_monthly": 0.1609, "return_since_inception": 57.8372,
    },
    "Alfalah Asset Allocation Fund": {
        "nav": 61.5965, "offer": 63.7216, "date": "06 May 2026",
        "return_monthly": -0.0204, "return_since_inception": -4.5447,
    },
    "Alfalah MTS Fund": {
        "nav": 113.4235, "offer": 116.0322, "date": "06 May 2026",
        "return_monthly": 0.1340, "return_since_inception": 25.8505,
    },
    "Alfalah Money Market Fund-II": {
        "nav": 112.3804, "offer": 114.9651, "date": "06 May 2026",
        "return_monthly": 0.1789, "return_since_inception": 27.9673,
    },
    "Alfalah Savings Growth Fund": {
        "nav": 112.4676, "offer": 115.0544, "date": "06 May 2026",
        "return_monthly": 0.2458, "return_since_inception": 35.8329,
    },
    "Alfalah Income & Growth Fund": {
        "nav": 126.5372, "offer": 129.4476, "date": "06 May 2026",
        "return_monthly": 0.1522, "return_since_inception": 26.4987,
    },
    "Alfalah Islamic Income Growth Fund": {
        "nav": 100.4555, "offer": 100.4555, "date": "06 May 2026",
        "return_monthly": 0.1377, "return_since_inception": 0.5503,
    },
    "Alfalah Financial Sector Opportunity Fund": {
        "nav": 127.0021, "offer": 129.9231, "date": "06 May 2026",
        "return_monthly": 0.1373, "return_since_inception": 26.9631,
    },
    "Alfalah Financial Value Fund - II": {
        "nav": 114.2408, "offer": 118.1821, "date": "06 May 2026",
        "return_monthly": 0.9557, "return_since_inception": 8.4766,
    },
    "Alfalah Stock Fund-II": {
        "nav": 80.5857, "offer": 83.3659, "date": "06 May 2026",
        "return_monthly": 0.7349, "return_since_inception": -17.7639,
    },
    "Alfalah Cash Fund-II": {
        "nav": 111.3116, "offer": 113.8718, "date": "06 May 2026",
        "return_monthly": 0.1371, "return_since_inception": 25.2781,
    },
    "Alfalah GHP KPK Employee Pension Fund - Money Market": {
        "nav": 137.2538, "offer": 137.2538, "date": "06 May 2026",
        "return_monthly": 10.0375, "return_since_inception": 15.5418,
    },
}

# Approximate annualised returns (%) used for projections.
# Derived from historical NAV data / return since inception estimates.
STATIC_RETURNS: dict[str, dict] = {
    "Alfalah GHP Money Market Fund":
        {"annualized_return": 9.98,  "1y": 9.98,  "3y": 9.5,  "5y": 8.9},
    "Alfalah GHP Cash Fund":
        {"annualized_return": 8.97,  "1y": 8.97,  "3y": 8.5,  "5y": 8.0},
    "Alfalah GHP Sovereign Fund":
        {"annualized_return": 11.94, "1y": 11.94, "3y": 10.8, "5y": 9.5},
    "Alfalah GHP Income Fund":
        {"annualized_return": 9.34,  "1y": 9.34,  "3y": 9.0,  "5y": 8.5},
    "Alfalah GHP Income Multiplier Fund":
        {"annualized_return": 10.59, "1y": 10.59, "3y": 9.8,  "5y": 9.2},
    "Alfalah GHP Alpha Fund":
        {"annualized_return": 28.0,  "1y": 1.2,   "3y": 20.0, "5y": 18.0},
    "Alfalah GHP Stock Fund":
        {"annualized_return": 35.0,  "1y": 1.3,   "3y": 28.0, "5y": 22.0},
    "Alfalah GHP Dedicated Equity Fund":
        {"annualized_return": 22.0,  "1y": 1.1,   "3y": 18.0, "5y": 15.0},
    "Alfalah GHP Value Fund":
        {"annualized_return": 32.0,  "1y": 1.0,   "3y": 25.0, "5y": 20.0},
    "Alfalah Consumer Index Exchange Traded Fund":
        {"annualized_return": 15.0,  "1y": 0.7,   "3y": 12.0, "5y": 10.0},
    "Alfalah Islamic Amdani Fund":
        {"annualized_return": 7.73,  "1y": 7.73,  "3y": 7.0,  "5y": 6.5},
    "Alfalah Islamic Money Market Fund":
        {"annualized_return": 8.59,  "1y": 8.59,  "3y": 8.0,  "5y": 7.5},
    "Alfalah GHP Islamic Income Fund":
        {"annualized_return": 9.49,  "1y": 9.49,  "3y": 8.8,  "5y": 8.2},
    "Alfalah GHP Islamic Stock Fund":
        {"annualized_return": 33.0,  "1y": 1.2,   "3y": 26.0, "5y": 20.0},
    "Alfalah GHP Islamic Dedicated Equity Fund":
        {"annualized_return": 20.0,  "1y": 1.1,   "3y": 16.0, "5y": 13.0},
    "Alfalah GHP Islamic Value Fund":
        {"annualized_return": 18.0,  "1y": 0.2,   "3y": 14.0, "5y": 11.0},
    "Alfalah GHP Pension Fund - Money Market":
        {"annualized_return": 9.97,  "1y": 9.97,  "3y": 9.2,  "5y": 8.7},
    "Alfalah GHP Islamic Pension - Debt":
        {"annualized_return": 9.87,  "1y": 9.87,  "3y": 9.1,  "5y": 8.5},
    "Alfalah GHP Islamic Pension - Equity":
        {"annualized_return": 30.0,  "1y": -0.9,  "3y": 24.0, "5y": 18.0},
    "Alfalah GHP Islamic Pension - Money Market":
        {"annualized_return": 25.0,  "1y": 8.96,  "3y": 20.0, "5y": 16.0},
    "Alfalah Government Securities Fund":
        {"annualized_return": 12.0,  "1y": 0.2,   "3y": 10.0, "5y": 9.0},
    "Alfalah Asset Allocation Fund":
        {"annualized_return": -0.5,  "1y": -0.02, "3y": -1.0, "5y": -0.5},
    "Alfalah MTS Fund":
        {"annualized_return": 9.5,   "1y": 0.1,   "3y": 8.5,  "5y": 7.8},
    "Alfalah Money Market Fund-II":
        {"annualized_return": 9.8,   "1y": 0.2,   "3y": 9.0,  "5y": 8.4},
    "Alfalah Savings Growth Fund":
        {"annualized_return": 10.5,  "1y": 0.2,   "3y": 9.8,  "5y": 9.0},
    "Alfalah Income & Growth Fund":
        {"annualized_return": 9.5,   "1y": 0.2,   "3y": 8.8,  "5y": 8.2},
    "Alfalah Financial Sector Opportunity Fund":
        {"annualized_return": 10.0,  "1y": 0.1,   "3y": 9.2,  "5y": 8.5},
    "Alfalah Financial Value Fund - II":
        {"annualized_return": 4.0,   "1y": 1.0,   "3y": 3.5,  "5y": 3.0},
    "Alfalah Stock Fund-II":
        {"annualized_return": -5.0,  "1y": 0.7,   "3y": -3.0, "5y": -2.0},
}
# fmt: on
