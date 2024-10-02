import aiohttp

async def get_usd_price(api_key) -> int:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://currencyapi.net/api/v1/rates?key={api_key}&output=JSON") as response:
            data = await response.json()
            return data['rates']['RUB']