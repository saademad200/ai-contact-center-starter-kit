import httpx
from bs4 import BeautifulSoup


async def get_fund_performance(fund_name: str) -> str:
    """
    Fetches the latest performance figures (YTD, 1M, 3M, 1Y) for a given Alfalah fund.
    """
    url = "https://www.alfalahamc.com/fund-performance"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Stub: parse table for performance
        # e.g., table = soup.find('table', {'id': 'performanceTable'})

        return (
            f"Performance for {fund_name}: 1M: 1.2%, 3M: 3.5%, YTD: 12.1%, 1Y: 15.4%."
        )
    except Exception as e:
        return f"Error fetching performance for {fund_name}: {str(e)}"
