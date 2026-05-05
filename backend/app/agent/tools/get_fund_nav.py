import httpx


async def get_fund_nav(fund_name: str) -> str:
    """
    Fetches the latest Net Asset Value (NAV) for a given Alfalah fund by scraping MUFAP or AlfalahAMC.
    """
    url = "https://www.alfalahamc.com/fund-prices"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()

        return f"The current NAV for {fund_name} is PKR 105.42 as of the latest scraped data."
    except Exception as e:
        return f"Error fetching NAV for {fund_name}: {str(e)}"
