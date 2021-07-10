# CREATE TABLE tag (guild_id bigint NOT NULL, name text NOT NULL, description text NOT NULL, creator text NOT NULL, created_at timestamp NOT NULL, uses int NOT NULL, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE);
import datetime


class Tag:
    def __init__(self, bot, guild_id, name, description, creator):
        self.bot = bot
        self.guild_id = guild_id
        self.name = name
        self.description = description
        self.creator = creator
        self.created_at = datetime.datetime.utcnow()
        self.uses = 0

    async def post(self):
        query = """INSERT INTO tag ( guild_id, name, description, creator, created_at, uses)
                    VALUES ( $1, $2, $3, $4, $5, $6)"""
        await self.bot.db.execute(
            query,
            self.guild_id,
            self.name,
            self.description,
            self.creator,
            self.created_at,
            self.uses,
        )
