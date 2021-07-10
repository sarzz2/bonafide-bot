# CREATE TABLE mod_logs(guild_id bigint NOT NULL, user_id text NOT NULL,moderator text NOT NULL, reason text, created_at timestamp NOT NULL,type text, case_no int,message_id bigint, duration int, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE);
import datetime


class ModLogs:
    def __init__(
        self,
        bot,
        guild_id,
        user_id,
        moderator,
        reason,
        type,
        case_no,
        message_id,
        duration,
    ):
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.moderator = moderator
        self.reason = reason
        self.created_at = datetime.datetime.utcnow()
        self.type = type
        self.case_no = case_no
        self.message_id = message_id
        self.duration = duration

    async def post(self):
        query = """INSERT INTO mod_logs ( guild_id, user_id, moderator, reason, created_at, type, case_no, message_id, duration)
                    VALUES ( $1, $2, $3, $4, $5, $6, $7, $8, $9)"""
        await self.bot.db.execute(
            query,
            self.guild_id,
            self.user_id,
            self.moderator,
            self.reason,
            self.created_at,
            self.type,
            self.case_no,
            self.message_id,
            self.duration,
        )

    async def update(self):
        query = (
            """UPDATE mod_logs SET reason = $3 WHERE guild_id = $1 and case_no = $2"""
        )
        await self.bot.db.execute(query, self.guild_id, self.case_no, self.reason)
