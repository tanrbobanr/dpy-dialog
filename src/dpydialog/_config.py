from discord.ext import commands
import discord
import typing
import time


VALID_FLAGS = ["bot", "identity_checkfn", "utx", "dialog_embed_base",
               "error_embed_base", "cancellable", "cancel_keyword", "skippable",
               "skip_keyword", "timeout"]


class Config:
    def __init__(self, bot: commands.Bot,
                 identity_checkfn: typing.Callable[[discord.Message], bool],
                 utx: commands.Context | discord.Interaction,
                 dialog_embed_base: dict | discord.Embed = None,
                 error_embed_base: dict | discord.Embed = None,
                 cancellable: bool = False, cancel_keyword: str = "cancel",
                 skippable: bool = False, skip_keyword: str = "skip",
                 timeout: typing.Optional[int | float] = None) -> None:
        self.bot = bot
        self.identity_checkfn = identity_checkfn
        self.utx = utx
        self.dialog_embed_base = dialog_embed_base or {}
        self.error_embed_base = error_embed_base or {"color": 0xeb4747}
        self.cancellable = cancellable
        self.cancel_keyword = cancel_keyword.lower().strip()
        self.skippable = skippable
        self.skip_keyword = skip_keyword.lower().strip()
        self.timeout = timeout
        self.bot = bot
    
    def override(self, **kwargs) -> "Config":
        if not kwargs:
            return self
        new_kwargs = {flag:getattr(self, flag) for flag in VALID_FLAGS}
        new_kwargs.update(kwargs)
        return Config(**new_kwargs)
    
    def itx(self, ignore: bool = False) -> discord.Interaction | None:
        if isinstance(self.utx, discord.Interaction):
            return self.utx
        if self.utx.interaction is not None:
            return self.utx.interaction
        if not ignore:
            raise ValueError("This Config object was not set up for use with "
                             "interactions")

    def ctx(self, ignore: bool = False) -> commands.Context | None:
        if isinstance(self.utx, commands.Context):
            return self.utx
        if not ignore:
            raise ValueError("This Config object was not set up for use with "
                             "contexts")

    def itx_sender(self, itx: discord.Interaction):
        if itx.response.is_done:
            return itx.followup.send
        return itx.response.send_message
    
    def ctx_sender(self, ctx: commands.Context):
        return ctx.send
    
    @property
    def best_sender(self):
        itx = self.itx(ignore=True)
        if itx:
            return self.itx_sender(itx)
        return self.ctx_sender(self.ctx())
    
    @property
    def timestamp(self) -> int | None:
        return self.timeout and time.time() + self.timeout
