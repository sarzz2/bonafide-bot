import asyncio
import collections

import discord


EmojiSettings = collections.namedtuple("EmojiSettings", "start back forward end close")

EMOJI_DEFAULT = EmojiSettings(
    start="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}",
    back="\N{BLACK LEFT-POINTING TRIANGLE}",
    forward="\N{BLACK RIGHT-POINTING TRIANGLE}",
    end="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}",
    close="\N{BLACK SQUARE FOR STOP}",
)


class Paginator:
    max_page_size = 2000

    def __init__(
        self, page_size: int = 1800, prefix: str = "```", suffix: str = "```", **kwargs
    ):
        self.page_size = page_size
        self.prefix = prefix
        self.suffix = suffix

        total_length = self.page_size + self._prefix_length + self._suffix_length

        if total_length > self.max_page_size:
            raise ValueError(
                f"Page Size is too large for this interface. "
                f"({total_length} > {self.max_page_size})"
            )

        self._pages = []

        self.clear()

    @classmethod
    def paginate(
        cls,
        content: str,
        *,
        page_size: int = 1800,
        prefix: str = "```",
        suffix: str = "```",
        **kwargs,
    ):
        paginator = cls(page_size=page_size, prefix=prefix, suffix=suffix, **kwargs)

        for line in content.splitlines():
            paginator.add_line(line)

        paginator.end_page()

        return paginator

    def clear(self):
        """Clears the paginator"""
        self._new_page()

        self._pages = []

        return self

    def _new_page(self):
        if self.prefix is not None:
            self._current_page = [self.prefix]
            self._count = len(self.prefix) + 1
        else:
            self._current_page = []
            self._count = 0

    def add_line(self, line: str = ""):
        """Paginates a line"""
        max_page_size = self.page_size - self._prefix_length - self._suffix_length - 2
        if len(line) > max_page_size:
            raise RuntimeError(f"Line exceeds maximum page size {max_page_size}")

        if self._count + len(line) + 1 > self.page_size - self._suffix_length:
            self.end_page()

        self._count += len(line) + 1
        self._current_page.append(line)

        return self

    def end_page(self):
        """Ends a page."""
        if self.suffix is not None:
            self._current_page.append(self.suffix)
        self._pages.append("\n".join(self._current_page))

        self._new_page()

        return self

    @property
    def pages(self):
        """Returns the pages paginated"""
        return self._pages

    @property
    def page_count(self):
        """Returns the length of the paginated pages"""
        return len(self._pages)

    @property
    def _prefix_length(self):
        """Returns the Length of the prefix"""
        return len(self.prefix) if self.prefix else 0

    @property
    def _suffix_length(self):
        """Returns the Length of the suffix"""
        return len(self.suffix) if self.suffix else 0


class ReactionPaginator(Paginator):
    """
    A custom reaction-based paginator
    """

    def __init__(self, bot, **kwargs):
        super().__init__(**kwargs)

        self.bot = bot

        self.message = None
        self._display_page = 0

        self.owner = kwargs.pop("owner", None)
        self.timeout = kwargs.pop("timeout", 7200)
        self.delete_message = kwargs.pop("delete_message", False)

        self.sent_page_reactions = False

        self.task = None

        self.emojis = kwargs.pop("emoji", EMOJI_DEFAULT)

        if self.page_size > self.max_page_size:
            raise ValueError(
                f"Paginator passed has too large of a page size for this interface. "
                f"({self.page_size} > {self.max_page_size})"
            )

    @property
    def send_kwargs(self) -> dict:
        display_page = self.display_page
        page_num = f"\nPage {display_page + 1}/{self.page_count}"
        content = self.pages[display_page] + page_num
        return {"content": content}

    async def send_to(self, destination: discord.abc.Messageable):
        self.message = await destination.send(**self.send_kwargs)

        if self.task:
            self.task.cancel()

        self.task = self.bot.loop.create_task(self.react_loop())

        if not self.sent_page_reactions and self.page_count > 1:
            await self.send_all_reactions()

        return self

    @property
    def display_page(self):
        self._display_page = max(0, min(self.page_count - 1, self._display_page))
        return self._display_page

    @display_page.setter
    def display_page(self, value):
        self._display_page = max(0, min(self.page_count - 1, value))

    async def react_loop(self):
        start, back, forward, end, close = self.emojis

        def check(payload: discord.RawReactionActionEvent):
            owner_check = not self.owner or payload.user_id == self.owner.id

            emoji = payload.emoji
            if isinstance(emoji, discord.PartialEmoji) and emoji.is_unicode_emoji():
                emoji = emoji.name

            tests = (
                owner_check,
                payload.message_id == self.message.id,
                emoji,
                emoji in self.emojis,
                payload.user_id != self.bot.user.id,
            )

            return all(tests)

        try:
            while not self.bot.is_closed():
                payload = await self.bot.wait_for(
                    "raw_reaction_add", check=check, timeout=self.timeout
                )

                emoji = payload.emoji
                if isinstance(emoji, discord.PartialEmoji) and emoji.is_unicode_emoji():
                    emoji = emoji.name

                if emoji == close:
                    await self.message.delete()
                    return

                if emoji == start:
                    self.display_page = 0
                elif emoji == end:
                    self.display_page = self.page_count - 1
                elif emoji == back:
                    self.display_page -= 1
                elif emoji == forward:
                    self.display_page += 1

                self.bot.loop.create_task(self.update())

                try:
                    await self.message.remove_reaction(
                        payload.emoji, discord.Object(id=payload.user_id)
                    )
                except discord.Forbidden:
                    pass

        except (asyncio.CancelledError, asyncio.TimeoutError):
            if self.delete_message:
                return await self.message.delete()

            for emoji in filter(None, self.emojis):
                try:
                    await self.message.remove_reaction(emoji, self.bot.user)
                except (discord.Forbidden, discord.NotFound):
                    pass

    async def send_all_reactions(self):
        for emoji in filter(None, self.emojis):
            try:
                await self.message.add_reaction(emoji)
            except discord.NotFound:
                break
        self.sent_page_reactions = True

    @property
    def closed(self):
        if not self.task:
            return False
        return self.task.done()

    async def update(self):
        if not self.message:
            return

        if not self.sent_page_reactions and self.page_count > 1:
            self.bot.loop.create_task(self.send_all_reactions())
            self.sent_page_reactions = True

        try:
            await self.message.edit(**self.send_kwargs)
        except discord.NotFound:
            if self.task:
                self.task.cancel()

    def add_line(self, line: str = ""):
        super().add_line(line)

        self.bot.loop.create_task(self.update())


class EmbedReactionPaginator(ReactionPaginator):
    def __init__(self, bot, embed=discord.Embed(), **kwargs):
        super().__init__(bot, **kwargs)
        self.embed = embed

    max_page_size = 2048

    @property
    def send_kwargs(self):
        display_page = self.display_page
        page_num = f"\nPage {display_page + 1}/{self.page_count}"
        content = self.pages[display_page]

        embed = self.embed
        embed.description = content
        embed.set_footer(text=page_num)

        return {"embed": embed}
