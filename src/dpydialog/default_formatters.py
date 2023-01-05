from . import _formatter
from . import types
import typing
import discord
import re
import mimetypes
import time


def plural(value: int | float) -> typing.Literal[""] | typing.Literal["s"]:
    return "s" if abs(value) == 1 else ""


class PromptFormatter(_formatter.Formatter[type[types.MISSING]]):
    def get_all(self, body: str, continue_keyword: str | None, length: int | None):
        return (self.preface(continue_keyword),
                self.body(body, length),
                self.checkfn(continue_keyword))

    def preface(self, continue_keyword: str | None):
        if not continue_keyword:
            return "This is a prompt dialog. Please read the below."
        return (f"This is a prompt dialog. Please read the below, and type '{continue_keyword}' "
                "once finished.")
    
    def body(self, body: str, length: int | None):
        if not length:
            return body
        
        # we add an extra second to make it more seemless; without, it
        # will often get to "2 seconds ago" before actually moving on
        return (f"{body}\n\n*This prompt will automatically continue "
                f"<t:{int(time.time() + length + 1)}:R>.*")
    
    def checkfn(self, continue_keyword: str | None):
        def cf(message: discord.Message) -> type[types.MISSING] | None:
            if (continue_keyword is not None and message.content
                and message.content.strip().lower() == continue_keyword):
                return types.MISSING
        return cf


class TextFormatter(_formatter.Formatter[str]):
    def get_all(self, embed_base: dict | discord.Embed, body: str | None):
        return (self.preface(body),
                self.body(body),
                self.checkfn(embed_base))

    def preface(self, body: str | None):
        return body and ("This is a text dialog and requires you to type your "
                         "response.")
    
    def body(self, body: str | None):
        return body or "Please type your response below."
    
    def checkfn(self, embed_base: dict):
        def cf(message: discord.Message) -> str | discord.Embed:
            if not message.content:
                return self.error_embed(embed_base,
                                        description=("*Your response must "
                                                     "include text.*"))
            return message.content
        return cf


class NumberFormatter(_formatter.Formatter[float]):
    def get_all(self, embed_base: dict | discord.Embed, body: str,
                min_value: int | float | None, max_value: int | float | None):
        return (self.preface(body, min_value, max_value),
                self.body(body, min_value, max_value),
                self.checkfn(embed_base, min_value, max_value))

    @staticmethod
    def _make_message(min_value: int | float | None, 
                      max_value: int | float | None, base_phrase: str,
                      end_phrase: str) -> str:
        if min_value is None and max_value is None:
            msg = f"{base_phrase} {end_phrase}"
        elif min_value is None and max_value is not None:
            msg = (f"{base_phrase} less than or equal to {max_value} "
                   f"{end_phrase}")
        elif min_value is not None and max_value is None:
            msg = (f"{base_phrase} greater than or equal to {min_value} "
                   f"{end_phrase}")
        elif min_value is not None and max_value is not None:
            msg = (f"{base_phrase} between {min_value} and {max_value} "
                   f"(inclusive) {end_phrase}")
        return msg

    def preface(self, body: str, min_value: int | float | None,
                max_value: int | float | None):
        if not body:
            return
        base = "This is a number dialog that requires you to type a number"
        end = "as your response."
        return self._make_message(min_value, max_value, base, end)

    def body(self, body: str, min_value: int | float | None,
             max_value: int | float | None):
        if body:
            return body
        base = "Please type a number"
        end = "as your response."
        return self._make_message(min_value, max_value, base, end)

    def checkfn(self, embed_base: dict | discord.Embed,
                min_value: int | float | None,
                max_value: int | float | None):
        def cf(message: discord.Message) -> float | discord.Embed:
            if not message.content:
                return self.error_embed(embed_base,
                                        description=("*Your response must "
                                                     "include text.*"))
            try:
                value = float(message.content.strip())
                if min_value is not None and max_value is not None:
                    assert max_value >= value >= min_value
                elif min_value is not None and max_value is None:
                    assert value >= min_value
                elif min_value is None and max_value is not None:
                    assert max_value >= value
                return value
            except (ValueError, AssertionError):
                body = self.body(None, min_value, max_value)
                return self.error_embed(embed_base, description=f"*{body}*")
        return cf


class ChoiceFormatter(_formatter.Formatter[tuple[tuple[str, ...],
                                           tuple[int, ...]]]):
    def get_all(self, embed_base: dict | discord.Embed, body: str | None, choices: list[str],
                keys: list[str] | None, min_choices: int | None, max_choices: int | None,
                remove_duplicates: bool):
        return (self.preface(min_choices, max_choices),
                self.body(body, choices, keys),
                self.checkfn(embed_base, choices, keys, min_choices,
                             max_choices, remove_duplicates))

    def preface(self, min_choices: int | None, max_choices: int | None):
        base = "This is a choice dialog that requires you to choose"
        end1 = ("of the following choices by typing their corresponding key "
                "(left of colon) as your response.")
        end2 = ("of the following choices by typing their corresponding keys "
                "(left of colon) separated by commas as your response.")
        if min_choices is None and max_choices is None:
            return f"{base} 1 {end1}"
        if min_choices is None and max_choices is not None:
            return f"{base} at most {max_choices} {end2}"
        if min_choices is not None and max_choices is None:
            return f"{base} at least {min_choices} {end2}"
        if (min_choices is not None and max_choices is not None
            and min_choices == max_choices):
            if min_choices == 1:
                return f"{base} {min_choices} {end1}"
            return f"{base} {min_choices} {end2}"
        if min_choices is not None and max_choices is not None:
            return (f"{base} between {min_choices} and {max_choices} "
                    f"(inclusive) {end2}")

    def body(self, body: str | None, choices: typing.Iterable[str],
             keys: typing.Iterable[str]):
        body_ = "\n".join([f"`{k}`: *{c}*" for c, k in zip(choices, keys)])
        if body:
            return f"{body}\n\n{body_}"
        return body_
    
    def checkfn(self, embed_base: dict, choices: list[str],
                keys: list[str] | None, min_choices: int | None,
                max_choices: int | None, remove_duplicates: bool):
        commas = re.compile(r"(?<!\\)(?:\s+)?,(?:\s+)?")
        def cf(message: discord.Message
               ) -> tuple[tuple[str, ...], tuple[int, ...]] | discord.Embed:
            if not message.content:
                return self.error_embed(embed_base,
                                        description=("*Your response must "
                                                     "include text.*"))
            if remove_duplicates:
                # we use `list(dict.fromkeys())` to remove duplicates while
                # preserving order; its slower than some other methods, but
                # simpler, and won't affect runtime in any significant way
                user_choices = list(dict.fromkeys(re.split(commas,
                                                           message.content)))
            else:
                user_choices = re.split(commas, message.content)


            # ensure all of user's choices are valid
            if not all(k in keys for k in user_choices):
                valid_keys = ", ".join(f"'{k}'" for k in keys)
                return self.error_embed(embed_base,
                                        description=("*All of your choices "
                                                     "must be valid keys "
                                                     "corresponding to one of"
                                                     " the above values. The "
                                                     "valid keys for the dialog"
                                                     f" are: {valid_keys}*"))

            # check to make sure number of user choices meet the requirements
            if (min_choices is not None and max_choices is not None
                and min_choices == max_choices
                and len(user_choices) != min_choices):
                return self.error_embed(embed_base,
                                        description=(f"*You must choose "
                                                     f"{min_choices} of "
                                                     "the above.*"))
            elif (min_choices is not None and max_choices is not None and not
                  max_choices >= len(user_choices) >= min_choices):
                return self.error_embed(embed_base,
                                        description=(f"*You must choose between"
                                                     f" {min_choices} and "
                                                     f"{max_choices} of the "
                                                     "above.*"))
            elif (min_choices is None and max_choices is not None and
                  len(user_choices) > max_choices):
                return self.error_embed(embed_base,
                                        description=(f"*You must choose at most"
                                                     f" {max_choices} of the "
                                                     "above.*"))
            elif (min_choices is not None and max_choices is None and
                  len(user_choices) < min_choices):
                return self.error_embed(embed_base,
                                        description=(f"*You must choose at "
                                                     f"least {min_choices} of "
                                                     "the above.*"))
            elif (min_choices is None and max_choices is None
                  and len(user_choices) != 1):
                return self.error_embed(embed_base,
                                        description=(f"*You must choose "
                                                     f"1 of "
                                                     "the above.*"))

            # prepare and return data
            indexes = [keys.index(k) for k in user_choices]
            values = [choices[i] for i in indexes]
            return tuple(values), tuple(indexes)
        return cf


class FileFormatter(_formatter.Formatter[list[discord.Attachment]]):
    def get_all(self, embed_base: dict | discord.Embed, body: str,
                attachments: list[discord.Attachment], min_files: int | None,
                max_files: int | None, allowed_mimetypes: typing.Iterable[str],
                allowed_extensions: typing.Iterable[str],
                finished_keyword: str):
        return (self.preface(body, min_files, max_files, allowed_mimetypes,
                             allowed_extensions, finished_keyword),
                self.body(body, min_files, max_files, allowed_mimetypes,
                          allowed_extensions, finished_keyword),
                self.checkfn(embed_base, attachments, min_files, max_files,
                             allowed_mimetypes, allowed_extensions,
                             finished_keyword))

    @staticmethod
    def _get_allowed_extensions(allowed_mimetypes: typing.Iterable[str],
                                allowed_extensions: typing.Iterable[str]
                                ) -> list[str]:
        allowed_extensions = list(allowed_extensions or [])
        if allowed_mimetypes:
            for ext, mtype in mimetypes.types_map.items():
                if (mtype in allowed_mimetypes
                    and ext not in allowed_extensions):
                    allowed_extensions.append(ext)
        return allowed_extensions

    @staticmethod
    def _make_message(min_files: int | None, max_files: int | None,
                      base_phrase: str, end_phrase: str) -> str:
        if min_files is None and max_files is None:
            msg = f"{base_phrase} any number of {end_phrase}"
        elif min_files is None and max_files is not None:
            msg = f"{base_phrase} at most {max_files} {end_phrase}"
        elif min_files is not None and max_files is None:
            msg = f"{base_phrase} at least {min_files} {end_phrase}"
        elif (min_files is not None and max_files is not None
            and min_files == max_files):
            return f"{base_phrase} {min_files} {end_phrase}"
        elif min_files is not None and max_files is not None:
            msg = (f"{base_phrase} between {max_files} and {max_files} "
                   f"(inclusive) {end_phrase}")
        return msg

    @staticmethod
    def _types_phrase(allowed_mimetypes: typing.Iterable[str],
                      allowed_extensions: typing.Iterable[str],
                      sidechar: str = "") -> str:
        allowed_extensions = FileFormatter._get_allowed_extensions(
                allowed_mimetypes, allowed_extensions)
        allowed_extensions = [f"{sidechar}{v}{sidechar}" for v in
                              allowed_extensions]
        if allowed_extensions:
            if len(allowed_extensions) == 1:
                return f" of type {allowed_extensions[0]}"
            if len(allowed_extensions) == 2:
                return (f" of type {allowed_extensions[0]}"
                        f" or {allowed_extensions[1]}")
            return (f" of type {', '.join(allowed_extensions[:-1])} or "
                    f"{allowed_extensions[-1]}")
        return ""

    def preface(self, body: str, min_files: int | None, max_files: int | None,
                allowed_mimetypes: typing.Iterable[str],
                allowed_extensions: typing.Iterable[str],
                finished_keyword: str):
        if not body:
            return
        types_phrase = self._types_phrase(allowed_mimetypes, allowed_extensions)
        base = "This is a file dialog that requires you to upload"
        end = (f"file(s){types_phrase}. Type '{finished_keyword}' once "
               "finished to complete the dialog.")
        return self._make_message(min_files, max_files, base, end)

    def body(self, body: str, min_files: int | None, max_files: int | None,
             allowed_mimetypes: typing.Iterable[str],
             allowed_extensions: typing.Iterable[str], finished_keyword: str):
        if body:
            return body
        types_phrase = self._types_phrase(allowed_mimetypes, allowed_extensions,
                                          "`")
        base = "Please upload"
        end = (f"file(s){types_phrase}. Type `{finished_keyword}` once "
               "finished to complete the dialog.")
        return self._make_message(min_files, max_files, base, end)

    def checkfn(self, embed_base: dict, attachments: list[discord.Attachment],
                min_files: int | None, max_files: int | None,
                allowed_mimetypes: typing.Iterable[str],
                allowed_extensions: typing.Iterable[str],
                finished_keyword: str):
        def cf(message: discord.Message
               ) -> list[discord.Attachment] | discord.Embed | None:
            # this one is pretty complex, so here are the basic events:
            # 1. ensure user is sending files unless they are finishing
            #    the dialog
            # 2. if sending files, ensure the number of files sent doesn't
            #    cause the total number of files to break past max_files
            # 3. if sending files and mimetypes/extensions have been defined,
            #    ensure all files have an allowed extension (mimetypes get
            #    turned into all their extensions)
            # 4. if the user is not finishing the dialog, simply return
            # 5. if the user is finishing the dialog, ensure the number of
            #    files sent meet the requirements (min_files and max_files)
            # 6. return the attachments
            _allowed_extensions = self._get_allowed_extensions(
                    allowed_mimetypes, allowed_extensions)
            
            # make sure there are attachments unless user is finishing dialog
            is_finishing = message.content is not None and message.content.strip().lower() == finished_keyword
            if not is_finishing and not message.attachments:
                return self.error_embed(embed_base, description=("*Unless finishing this dialog, your message must contain one or more files.*"))

            # make sure user isn't surpassing max number of files
            if message.attachments:
                if max_files is not None and len(message.attachments) + len(attachments) > max_files:
                    if len(attachments) == max_files:
                        return self.error_embed(embed_base, description=f"*You have already reached the maximum number of files allowed by this dialog. Please type `{finished_keyword}` to finish.*")
                    return self.error_embed(embed_base, description=f"*Addition of these files would surpass the maximum number of files allowed by this dialog. You may send at most {max_files - len(attachments)} more file(s).*")
            
            # ensure filetypes are correct
            if _allowed_extensions and message.attachments:
                for attachment in message.attachments:
                    filename = attachment.filename.lower()
                    if not any(ext in filename for ext in _allowed_extensions):
                        type_phrase = self._types_phrase(allowed_mimetypes,
                                                         allowed_extensions)
                        return self.error_embed(embed_base, description=
                                f"*All files sent must be {type_phrase}.*")
            attachments.extend(message.attachments)
            
            if not is_finishing:
                return # causes loop to continue to another wait_for

            # make final checks if user is finishing the dialog;
            # we don't need to do any max_files checks because that
            # is already happening each time the user sends attachments
            num_attachments = len(attachments)
            if min_files is not None and max_files is not None and min_files == max_files and num_attachments != min_files:
                return self.error_embed(embed_base, description=f"*You must have sent exactly {min_files} file(s) in order to finish this dialog. You have sent a total of {num_attachments}.*")
            elif min_files is not None and max_files is not None and not max_files >= num_attachments >= min_files:
                return self.error_embed(embed_base, description=f"*You must have sent between {min_files} and {max_files} file(s) in order to finish this dialog. You have sent a total of {num_attachments}.*")
            elif min_files is not None and num_attachments < min_files:
                return self.error_embed(embed_base, description=f"*You must have sent at least {min_files}. You have sent a total of {num_attachments}.*")

            # return the total attachments
            return attachments
        return cf
