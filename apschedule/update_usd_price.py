from utils.get_usd_price import get_usd_price
from db.database import set_usd_price

async def update_usd_price(config):
   usd_rate = await get_usd_price(config.settings.currency_token)
   await set_usd_price(usd_rate)