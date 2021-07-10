# CREATE TABLE bonafidecoin (guild_id bigint, user_id bigint, wallet int, bank int, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE);


class BonfideCoin:
    def __init__(
        self,
        bot,
    ):
        self.bot = bot

    async def post(self, guild_id: int, user_id: int, wallet: int, bank: int):
        query = """INSERT INTO bonafidecoin ( guild_id, user_id, wallet, bank)
                    VALUES ( $1, $2, $3, $4)"""
        await self.bot.db.execute(query, guild_id, user_id, wallet, bank)

    async def get(self, guild_id: int, user_id: int):
        query = """ SELECT * FROM bonafidecoin WHERE guild_id = $1 AND user_id = $2"""
        return await self.bot.db.fetch_row(query, guild_id, user_id)
