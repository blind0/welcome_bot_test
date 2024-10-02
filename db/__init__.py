import aiosqlite


class db_manager():
    __pool = None

    @classmethod
    async def init(cls, db_name) -> None:
        cls.__pool = await aiosqlite.connect(db_name)

    @classmethod
    async def create_schema(cls):
        table_query =  """
                CREATE TABLE IF NOT EXISTS settings_table (
                    name TEXT PRIMARY KEY,
                    data INTEGER NOT NULL
                );
            """
        
        await cls.execute_commit_query(table_query)

    @classmethod
    async def execute_query(cls, query, params=None):
        async with cls.__pool.cursor() as cur:
            if params is None:
                await cur.execute(query)
            else:
                await cur.execute(query, params)
            rows = await cur.fetchall()
        return rows
    
    @classmethod
    async def execute_commit_query(cls, query, params=None):
            if params is None:
                await cls.__pool.execute(query)
            else:
                await cls.__pool.execute(query, params)
            await cls.__pool.commit()