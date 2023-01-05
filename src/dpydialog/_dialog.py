from ._config import Config
from ._runner import Runner
from ._formatter import Formatter
from . import default_formatters
from . import exceptions
from . import types
import discord
import typing


class Dialog:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.exceptions = (exceptions.Cancelled, exceptions.TimedOut)
    
    @staticmethod
    def _dialog_embed(title: str, preface: str | None, body: str,
                      cfg: Config, formatter: Formatter) -> discord.Embed:
        return formatter.dialog_embed(title, preface, body, cfg.timestamp,
                                      cfg.cancellable, cfg.skippable,
                                      cfg.cancel_keyword, cfg.skip_keyword,
                                      cfg.dialog_embed_base)

    async def error(self, exc: Exception) -> None:
        formatter = Formatter()
        if isinstance(exc, exceptions.Cancelled):
            embed = formatter.error_embed(self.cfg.error_embed_base,
                                          description = "*This command has been cancelled.*")
        elif isinstance(exc, exceptions.TimedOut):
            embed = formatter.error_embed(self.cfg.error_embed_base,
                                          description = "*This command has timed out.*")
        else:
            raise exc from exc
        await self.cfg.best_sender(embed=embed)

    async def prompt(self, title: str, body: str, length: int = None,
                     continue_keyword: str | None = "continue",
                     formatter: Formatter[type[types.MISSING]] = ..., **cfg_overrides) -> None:
        if length is None and continue_keyword is None:
            raise ValueError("one of 'length' or 'continue_keyword' must not be None")
        cfg = self.cfg.override(**cfg_overrides)
        if formatter == ...:
            formatter = default_formatters.PromptFormatter()
        preface, body, checkfn = formatter.get_all(body, continue_keyword, length)

        embed = self._dialog_embed(title, preface, body, cfg, formatter)
        await cfg.best_sender(embed=embed)

        # override cfg again after main embed is sent so the
        # "automatically cancelled in..." str isn't appended to the end of it
        cfg2 = cfg.override(timeout=length)
        runner: Runner[type[types.MISSING]] = Runner(cfg2)

        # runner.run will raise TimedOut if it reaches the timeout
        try:
            message, value = await runner.run(checkfn)
        except exceptions.TimedOut:
            return

    async def text(self, title: str, body: str = None,
                   formatter: Formatter[str] = ..., **cfg_overrides) -> str:
        cfg = self.cfg.override(**cfg_overrides)
        if formatter == ...:
            formatter = default_formatters.TextFormatter()
        preface, body, checkfn = formatter.get_all(cfg.error_embed_base, body)

        embed = self._dialog_embed(title, preface, body, cfg, formatter)
        await cfg.best_sender(embed=embed)

        runner: Runner[str] = Runner(cfg)
        message, value = await runner.run(checkfn)
        return value

    async def number(self, title: str, body: str = None,
                     min_value: int | float = None,
                     max_value: int | float = None,
                     formatter: Formatter[float] = ...,
                     **cfg_overrides) -> float:
        cfg = self.cfg.override(**cfg_overrides)
        if formatter == ...:
            formatter = default_formatters.NumberFormatter()
        preface, body, checkfn = formatter.get_all(cfg.error_embed_base, body,
                                                   min_value, max_value)

        embed = self._dialog_embed(title, preface, body, cfg, formatter)
        await cfg.best_sender(embed=embed)

        runner: Runner[float] = Runner(cfg)
        message, value = await runner.run(checkfn)
        return value

    # pending: add `use_itx` option to use views
    async def choice(self, title: str, choices: typing.Iterable[str], body: str = None,
                     min_choices: int = None, max_choices: int = None,
                     keys: typing.Iterable[str] = None, remove_duplicates: bool = True,
                     formatter: Formatter[tuple[tuple[str, ...], tuple[int, ...]]] = ...,
                     **cfg_overrides) -> tuple[tuple[str, ...], tuple[int, ...]]:
        if not keys:
            keys = [str(i) for i in range(1, len(choices) + 1)]
        cfg = self.cfg.override(**cfg_overrides)
        if formatter == ...:
            formatter = default_formatters.ChoiceFormatter()
        preface, body, checkfn = formatter.get_all(cfg.error_embed_base, body, list(choices),
                                                   list(keys), min_choices, max_choices,
                                                   remove_duplicates)

        embed = self._dialog_embed(title, preface, body, cfg, formatter)
        await cfg.best_sender(embed=embed)

        runner: Runner[tuple[tuple[str, ...], tuple[int, ...]]] = Runner(cfg)
        message, value = await runner.run(checkfn)
        return value
    
    async def file(self, title: str, body: str = None, min_files: int = None,
                   max_files: int = None,
                   allowed_mimetypes: typing.Iterable[str] = None,
                   allowed_extensions: typing.Iterable[str] = None,
                   finished_keyword: str = "done",
                   formatter: Formatter[list[discord.Attachment]] = ...,
                   **cfg_overrides) -> list[discord.Attachment]:
        cfg = self.cfg.override(**cfg_overrides)
        if formatter == ...:
            formatter = default_formatters.FileFormatter()
        preface, body, checkfn = formatter.get_all(cfg.error_embed_base, body,
                                                   [], min_files, max_files,
                                                   allowed_mimetypes,
                                                   allowed_extensions,
                                                   finished_keyword)

        embed = self._dialog_embed(title, preface, body, cfg, formatter)
        await cfg.best_sender(embed=embed)

        runner: Runner[list[discord.Attachment]] = Runner(cfg)
        message, value = await runner.run(checkfn)
        return value

# class Context:
#     def __init__(self, __cfg: Config) -> None:
#         self._cfg = __cfg

#     @staticmethod
#     async def _send_embed(__cfg: Config, __embed: discord.Embed) -> None:
#         if __cfg.ctx.interaction:
#             await __cfg.ctx.interaction.response.send_message(embed=__embed)
#         else:
#             await __cfg.ctx.send(embed=__embed)
    
#     @staticmethod
#     def _get_ts(__cfg: Config) -> float:
#         return __cfg.timeout and time.time() + __cfg.timeout

#     async def text(self, title: str, body: str = None,
#                    **cfg_overrides) -> str | exceptions.Skipped:
#         cfg = self._cfg._override(**cfg_overrides)
#         assert cfg.ctx, "a discord.ext.commands.Context instance is required"
#         preface, body = getpb_text(body)
#         ts = self._get_ts(cfg)

#         embed = cfg.embed_wrapper_fn(cfg, title, preface, body, ts)
#         await self._send_embed(cfg, embed)

#         message, value = await ctxloop(cfg, ts, makecf_text(cfg))
#         return value
    
#     async def number(self, title: str, min_value: int | float | None = None,
#                      max_value: int | float | None = None, body: str = None,
#                      **cfg_overrides) -> float | exceptions.Skipped:
#         if min_value is not None and max_value is not None:
#             assert max_value > min_value, "max_value must be less than min_value"
#         cfg = self._cfg._override(**cfg_overrides)
#         assert cfg.ctx, "a discord.ext.commands.Context instance is required"
#         preface, body = getpb_number(body, min_value, max_value)
#         ts = self._get_ts(cfg)

#         embed = cfg.embed_wrapper_fn(cfg, title, preface, body, ts)
#         await self._send_embed(cfg, embed)

#         message, value = await ctxloop(cfg, ts, makecf_number(cfg, min_value,
#                                                        max_value))
#         return value
    
#     async def choice(self, title: str, choices: list[str], min_choices: int = None, max_choices: int = None, **cfg_overrides) -> list[int]:
#         if len(choices) < 2:
#             raise ValueError("at least two choices must be provided")
#         if max_choices and max_choices > len(choices):
#             raise ValueError("max_choices must be less than or equal to the "
#                              "number of provided choices")
#         if min_choices and (min_choices < 1 or len(choices) < min_choices):
#             raise ValueError("min_choices must be greater than or equal to 1 "
#                              "and the number of provided choices must be at "
#                              "least that of min_choices")
#         cfg = self._cfg._override(**cfg_overrides)
#         assert cfg.ctx, "a discord.ext.commands.Context instance is required"
#         preface, _ = getpb_choice(min_choices, max_choices)
#         body = make_choice_body(choices)
#         ts = self._get_ts(cfg)

#         embed = cfg.embed_wrapper_fn(cfg, title, preface, body, ts)
#         await self._send_embed(cfg, embed)

#         message, value = await ctxloop(cfg, ts, makecf_choice(cfg, choices, min_choices, max_choices))
#         return value
        

        
            



