guild = """CREATE TABLE IF NOT EXISTS guild (guild_id bigint NOT NULL, guild_name varchar(100) NOT NULL,
prefix varchar(5), server_log bigint, mod_log bigint, ignored_channel bigint[], lockdown_channel bigint[],
filter_ignored_channel bigint[], profanity_check boolean DEFAULT false, invite_link boolean DEFAULT false,
PRIMARY KEY(guild_id))"""

bonafidecoin = """CREATE TABLE IF NOT EXISTS bonafidecoin (guild_id bigint NOT NULL, user_id bigint NOT NULL,
wallet int, bank int, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE)"""

cog_check = """CREATE TABLE IF NOT EXISTS cog_check (guild_id bigint NOT NULL, cog_name text, enabled boolean,
 CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE)"""

filter = """CREATE TABLE IF NOT EXISTS filter (guild_id bigint NOT NULL, keyword text UNIQUE, CONSTRAINT fk_guild
FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE) """

level = """CREATE TABLE IF NOT EXISTS level(guild_id bigint NOT NULL, user_id bigint NOT NULL, total_xp int,
current_xp int, required_xp int, lvl int, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id)
ON DELETE CASCADE) """

mod_logs = """CREATE TABLE IF NOT EXISTS mod_logs(guild_id bigint NOT NULL, user_id bigint NOT NULL, moderator
bigint NOT NULL, reason text, created_at timestamp, type text, case_no int, message_id bigint,
duration timestamp, action boolean DEFAULT true, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(
guild_id) ON DELETE CASCADE) """

roles = """CREATE TABLE IF NOT EXISTS roles (guild_id bigint NOT NULL, user_id bigint NOT NULL, role_id bigint
NOT NULL, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE) """

shop = """CREATE TABLE IF NOT EXISTS shop (guild_id bigint NOT NULL, items text UNIQUE, value int, role_id bigint,
description text, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE) """

stats = """CREATE TABLE IF NOT EXISTS stats (guild_id bigint NOT NULL, user_id bigint NOT NULL, message_count
int, created_at timestamp, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE
CASCADE) """

stats_server = """CREATE TABLE IF NOT EXISTS stats_server(guild_id bigint, member_count int, created_at date,
CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE) """

tags = """CREATE TABLE IF NOT EXISTS tag(guild_id bigint NOT NULL, creator bigint NOT NULL, name text UNIQUE,
description text, created_at timestamp, uses int, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(
guild_id) ON DELETE CASCADE) """

user_inventory = """CREATE TABLE IF NOT EXISTS stats (guild_id bigint NOT NULL, user_id bigint NOT NULL,
items text, value int, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE) """

role_check = """CREATE TABLE IF NOT EXISTS role_check (guild_id bigint, cog_name text, role_id bigint,
enabled boolean, CONSTRAINT fk_guild FOREIGN KEY(guild_id) REFERENCES guild(guild_id) ON DELETE CASCADE); """
