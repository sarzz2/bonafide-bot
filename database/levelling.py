# CREATE TABLE level(guild_id bigint, user_id bigint, total_xp int,  current_xp int, required_xp int,CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE);


class Level:
    def __init__(self, bot, guild_id, user, total_xp, current_xp, required_xp, lvl):
        self.bot = bot
        self.guild_id = guild_id
        self.user = user
        self.total_xp = total_xp
        self.current_xp = current_xp
        self.required_xp = required_xp
        self.lvl = lvl

    async def post(self):
        query = """INSERT INTO level (guild_id, user_id, total_xp, current_xp, required_xp, lvl) VALUES($1, $2, $3,
        $4, $5, $6)"""
        await self.bot.db.execute(
            query,
            self.guild_id,
            self.user,
            self.total_xp,
            self.current_xp,
            self.required_xp,
            self.lvl,
        )
