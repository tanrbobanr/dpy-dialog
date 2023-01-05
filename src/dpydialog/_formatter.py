from . import types
from . import constants
import discord
import typing



class Formatter(typing.Generic[types.VT]):
    def get_all(self, *args, **kwargs
                ) -> tuple[str | None, str, typing.Callable[[discord.Message],
                                                            typing.Union[
                                                                types.VT,
                                                                discord.Embed
                                                            ]]]:
        raise NotImplementedError()

    # def get_preface_and_body(self, *args, **kwargs) -> tuple[str | None, str]:
    #     raise NotImplementedError()

    def preface(self, *args, **kwargs) -> str | None:
        raise NotImplementedError()
    
    def body(self, *args, **kwargs) -> str:
        raise NotImplementedError()

    def checkfn(self, *args, **kwargs) -> typing.Callable[[discord.Message],
                                                          typing.Union[
                                                              types.VT,
                                                              discord.Embed,
                                                              None
                                                          ]]:
        raise NotImplementedError()

    def error_embed(self, embed_base: discord.Embed | dict,
                    **kwargs) -> discord.Embed:
        if isinstance(embed_base, discord.Embed):
            embed_dict = embed_base.to_dict()
        else:
            embed_dict = dict(embed_base)
        embed_dict.update(kwargs)
        embed = discord.Embed.from_dict(embed_dict)
        if constants.CREATOR_REFERENCE:
            embed.set_footer(text=constants.CREATOR_REFERENCE)
        return embed

    def dialog_embed(self, title: str, preface: str, body: str,
                     timestamp: float | None, cancellable: bool,
                     skippable: bool, cancel_keyword: str, skip_keyword: str,
                     embed_base: discord.Embed | dict) -> discord.Embed:
        """Create and return a `discord.Embed` object based on various criteria.
        
        """
        buf: list[str] = []

        # preface and body
        if preface:
            buf.append(f"*`{preface}`*")
        buf.append(body)

        # cancel message and skip message
        cancel_msg = f"**`{cancel_keyword}`** to cancel"
        skip_msg = f"**`{skip_keyword}`** to skip"
        if cancellable and skippable:
            postface = f"You may type {cancel_msg} or {skip_msg}."
        elif cancellable:
            postface = f"You may type {cancel_msg}."
        elif skippable:
            postface = f"You may type {skip_msg}."
        else:
            postface = ""
        
        # auto cancel message (appended to postface)
        if timestamp:
            if postface:
                postface += " "
            postface += ("This dialog will be automatically cancelled "
                        f"<t:{int(timestamp)}:R> if not responded to.")
        
        # add postface to buffer
        if postface:
            buf.append(f"*{postface}*")
        
        # get base embed dict
        if isinstance(embed_base, discord.Embed):
            embed_dict = embed_base.to_dict()
        else:
            embed_dict = dict(embed_base)
        
        # add to base embed dict and return new embed
        embed_dict["title"] = title
        embed_dict["description"] = "\n\n".join(buf)
        embed = discord.Embed.from_dict(embed_dict)
        if constants.CREATOR_REFERENCE:
            embed.set_footer(text=constants.CREATOR_REFERENCE)
        return embed
