from db import db_manager

async def set_usd_price(amount):
    await db_manager.execute_commit_query(f"INSERT OR REPLACE INTO settings_table VALUES('usd_rate', '{amount}')")

async def get_usd_price() -> int:
    usd_rate = await db_manager.execute_query("SELECT * FROM settings_table WHERE name='usd_rate'")
    return usd_rate[0][1]