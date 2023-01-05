from . import exceptions
from . import _config
from . import types
import discord
import asyncio
import typing
import time


class Runner(typing.Generic[types.VT]):
    def __init__(self, cfg: _config.Config) -> None:
        self.cfg = cfg
    
    async def run(self, checkfn: typing.Callable[[discord.Message],
                                                 typing.Union[
                                                     types.VT,
                                                     discord.Embed
                                                 ]]
                  ) -> tuple[discord.Message, types.VT]:
        timestamp = self.cfg.timeout and time.time() + self.cfg.timeout
        try:
            while True:
                # get the new timeout
                if timestamp:
                    timeout = timestamp - time.time()
                    if timeout < 2:
                        raise exceptions.TimedOut(time.time())
                else:
                    timeout = None

                # wait for message and get content
                message: discord.Message = await self.cfg.bot.wait_for(
                        "message", check=self.cfg.identity_checkfn,
                        timeout=timeout)
                content = message.content and message.content.lower().strip()
                
                # handle cancel or skip
                if self.cfg.cancellable and content == self.cfg.cancel_keyword:
                    raise exceptions.Cancelled(message, time.time())
                if self.cfg.skippable and content == self.cfg.skip_keyword:
                    return message, None

                # ensure value passes check
                checkval = checkfn(message)
                if isinstance(checkval, discord.Embed):
                    await self.cfg.best_sender(embed=checkval)
                    continue
                if checkval == None:
                    continue
                
                # return message and value
                return message, checkval
        except asyncio.TimeoutError as exc:
            # `commands.Bot.wait_for` raises an asyncio.TimeoutError if
            # the time passed is greater than the provided timeout. Here
            # we simply catch that error and re-raise it as an
            # `exceptions.TimedOut` error for consistency
            raise exceptions.TimedOut(None, time.time()) from exc
