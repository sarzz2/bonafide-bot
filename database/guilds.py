#  CREATE TABLE guild(guild_id bigint, guild_name text, PRIMARY KEY(guild_id));


class Guild:
    def __init__(
        self,
        bot,
        guild_id: int,
        name: str,
        prefix=".",
        server_log: int = None,
        mod_log: int = None,
    ):
        self.bot = bot
        self.guild_id = guild_id
        self.name = name
        self.prefix = prefix
        self.server_log = server_log
        self.mod_log = mod_log

    async def post(self):
        query = """INSERT INTO guild ( guild_id, guild_name, prefix, server_log, mod_log)
                    VALUES ( $1, $2, $3, $4, $5)"""
        await self.bot.db.execute(
            query, self.guild_id, self.name, self.prefix, self.server_log, self.mod_log
        )
