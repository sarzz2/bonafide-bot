class Filter:
    def __init__(self, bot):
        self.bot = bot

    async def get(self, guild_id: int, keyword: str):
        query = """SELECT * FROM filter WHERE guild_id = $1 AND keyword =$2"""
        return await self.bot.db.fetch_row(query, guild_id, keyword)

    async def post(self, guild_id: int, keyword: str):
        query = """INSERT INTO filter (guild_id, keyword) VALUES($1, $2)"""
        await self.bot.db.execute(query, guild_id, keyword)

    async def delete(self, guild_id: int, keyword: str):
        query = """DELETE FROM filter WHERE guild_id = $1 AND keyword = $2"""
        await self.bot.db.execute(query, guild_id, keyword)
