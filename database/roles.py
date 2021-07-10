# CREATE TABLE roles(guild_id bigint NOT NULL, user_id bigint NOT NULL, role_id bigint NOT NULL, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE);
class Roles:
    def __init__(self, bot, guild_id: int, user_id: int, roles: str):

        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.role = roles

    async def post(self):
        query = """INSERT INTO roles ( guild_id, user_id, role_id)
                   VALUES ( $1, $2, $3)"""
        await self.bot.db.execute(query, self.guild_id, self.user_id, self.role)

    async def delete(self):
        query = """DELETE FROM roles WHERE guild_id = $1 AND user_id = $2"""
        await self.bot.db.execute(query, self.guild_id, self.user_id)
