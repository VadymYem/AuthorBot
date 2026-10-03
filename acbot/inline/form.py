import contextlib
import copy
import logging
import os
import random
import re
import time
import traceback
import typing
from asyncio import Event
from urllib.parse import urlparse

import grapheme
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultAudio,
    InlineQueryResultDocument,
    InlineQueryResultGif,
    InlineQueryResultLocation,
    InlineQueryResultPhoto,
    InlineQueryResultVideo,
    InputTextMessageContent,
)
from herokutl.errors.rpcerrorlist import ChatSendInlineForbiddenError
from herokutl.extensions.html import CUSTOM_EMOJIS
from herokutl.tl.types import Message

from .. import utils
from ..branding import photo_result
from ..types import AuthorBotReplyMarkup
from .types import InlineMessage, InlineUnit

logger = logging.getLogger(__name__)

VERIFICATION_EMOJIES = list(
    grapheme.graphemes(
        "👨‍🏫👩‍🏫👨‍🎤🧑‍🎤👩‍🎤👨‍🎓👩‍🎓👩‍🍳👩‍🌾👩‍⚕️🕵️‍♀️💂‍♀️👷‍♂️👮‍♂️👴🧑‍🦳👩‍🦳👱‍♀️👩‍🦰👨‍🦱👩‍⚖️🧙‍♂️🧝‍♀️🧛‍♀️"
        "🎅🧚‍♂️🙆‍♀️🙍‍♂️👩‍👦🧶🪢🪡🧵🩲👖👕👚🦺👗👙🩱👘🥻🩴🥿🧦🥾👟👞"
        "👢👡👠🪖👑💍👝👛👜💼🌂🥽🕶👓🧳🎒🐶🐱🐭🐹🐰🦊🐻🐷🐮"
        "🦁🐯🐨🐻‍❄️🐼🐽🐸🐵🙈🙉🙊🐒🦆🐥🐣🐤🐦🐧🐔🦅🦉🦇🐺🐗🐴"
        "🦄🐜🐞🐌🦋🐛🪱🐝🪰🪲🪳🦟🦗🕷🕸🐙🦕🦖🦎🐍🐢🦂🦑🦐🦞"
        "🦀🐡🐠🐟🐅🐊🦭🦈🐋🐳🐬🐆🦓🦍🦧🦣🐘🦛🐃🦬🦘🦒🐫🐪🦏"
        "🐂🐄🐎🐖🐏🐑🦙🐈🐕‍🦺🦮🐩🐕🦌🐐🐈‍⬛🪶🐓🦃🦤🦚🦜🦡🦨🦝🐇"
        "🕊🦩🦢🦫🦦🦥🐁🐀🐿🦔🌳🌲🌵🐲🐉🐾🎋🍂🍁🍄🐚🌾🪨💐🌷"
        "🥀🌺🌸🌻🌞🌜🌘🌗🌎🪐💫⭐️✨⚡️☄️💥☀️🌪🔥🌈🌤⛅️❄️⛄️🌊"
        "☂️🍏🍎🍐🍊🍋🍌🍉🥭🍑🍒🍈🫐🍓🍇🍍🥥🥝🍅🥑🥦🧔‍♂️"
    )
)


class Placeholder:
    """Placeholder"""


class Form(InlineUnit):
    async def form(
        self,
        text: str,
        message: typing.Union[Message, int],
        reply_markup: typing.Optional[AuthorBotReplyMarkup] = None,
        *,
        force_me: bool = False,
        always_allow: typing.Optional[typing.List[int]] = None,
        manual_security: bool = False,
        disable_security: bool = False,
        ttl: typing.Optional[int] = None,
        on_unload: typing.Optional[callable] = None,
        photo: typing.Optional[str] = None,
        gif: typing.Optional[str] = None,
        file: typing.Optional[str] = None,
        mime_type: typing.Optional[str] = None,
        video: typing.Optional[str] = None,
        location: typing.Optional[str] = None,
        audio: typing.Optional[typing.Union[dict, str]] = None,
        silent: bool = False,
        rich_html: typing.Optional[str] = None,
    ) -> typing.Union[InlineMessage, bool]:
        """
        Send inline form to chat
        :param text: Content of inline form. HTML markdown supported
        :param rich_html: Native Rich Message HTML, with `text` as the classic fallback
        :param message: Where to send inline. Can be either `Message` or `int`
        :param reply_markup: List of buttons to insert in markup. List of dicts with keys: text, callback
        :param force_me: Either this form buttons must be pressed only by owner scope or no
        :param always_allow: Users, that are allowed to press buttons in addition to previous rules
        :param ttl: Time, when the form is going to be unloaded. Unload means, that the form
                    buttons with inline queries and callback queries will become unusable, but
                    buttons with type url will still work as usual. Pay attention, that ttl can't
                    be bigger, than default one (1 day) and must be either `int` or `False`
        :param on_unload: Callback, called when form is unloaded and/or closed. You can clean up trash
                          or perform another needed action
        :param manual_security: By default, AuthorBot will try to inherit inline buttons security from the caller (command)
                                If you want to avoid this, pass `manual_security=True`
        :param disable_security: By default, AuthorBot will try to inherit inline buttons security from the caller (command)
                                 If you want to disable all security checks on this form in particular, pass `disable_security=True`
        :param photo: Attach a photo to the form. URL must be supplied
        :param gif: Attach a gif to the form. URL must be supplied
        :param file: Attach a file to the form. URL must be supplied
        :param mime_type: Only needed, if `file` field is not empty. Must be either 'application/pdf' or 'application/zip'
        :param video: Attach a video to the form. URL must be supplied
        :param location: Attach a map point to the form. List/tuple must be supplied (latitude, longitude)
                         Example: (55.749931, 48.742371)
                         ⚠️ If you pass this parameter, you'll need to pass empty string to `text` ⚠️
        :param audio: Attach a audio to the form. Dict or URL must be supplied
        :param silent: Whether the form must be sent silently (w/o "Opening form..." message)
        :return: If form is sent, returns :obj:`InlineMessage`, otherwise returns `False`
        """
        with contextlib.suppress(AttributeError):
            _acbot_client_id_logging_tag = copy.copy(self._client.tg_id)  # noqa: F841

        if reply_markup is None:
            reply_markup = []

        if always_allow is None:
            always_allow = []

        if not isinstance(text, str):
            logger.error(
                "Invalid type for `text`. Expected `str`, got `%s`",
                type(text),
            )
            return False

        if rich_html is not None and not isinstance(rich_html, str):
            logger.error("Invalid type for `rich_html`. Expected `str`")
            return False

        text = self.sanitise_text(text)

        if not isinstance(silent, bool):
            logger.error(
                "Invalid type for `silent`. Expected `bool`, got `%s`",
                type(silent),
            )
            return False

        if not isinstance(manual_security, bool):
            logger.error(
                "Invalid type for `manual_security`. Expected `bool`, got `%s`",
                type(manual_security),
            )
            return False

        if not isinstance(disable_security, bool):
            logger.error(
                "Invalid type for `disable_security`. Expected `bool`, got `%s`",
                type(disable_security),
            )
            return False

        if not isinstance(message, (Message, int)):
            logger.error(
                "Invalid type for `message`. Expected `Message` or `int`, got `%s`",
                type(message),
            )
            return False

        if not isinstance(reply_markup, (list, dict)):
            logger.error(
                "Invalid type for `reply_markup`. Expected `list` or `dict`, got `%s`",
                type(reply_markup),
            )
            return False

        if photo and (
            not isinstance(photo, str)
            or not (utils.check_url(photo) or re.fullmatch(r"[A-Za-z0-9_-]{20,}", photo))
        ):
            logger.error(
                "Invalid type for `photo`. Expected `str` with URL, got `%s`",
                type(photo),
            )
            return False

        try:
            path = urlparse(photo).path
            ext = os.path.splitext(path)[1]
        except Exception:
            ext = None

        if photo is not None and ext in {".gif", ".mp4"}:
            gif = copy.copy(photo)
            photo = None

        if gif and (not isinstance(gif, str) or not utils.check_url(gif)):
            logger.error(
                "Invalid type for `gif`. Expected `str` with URL, got `%s`",
                type(gif),
            )
            return False

        if file and (not isinstance(file, str) or not utils.check_url(file)):
            logger.error(
                "Invalid type for `file`. Expected `str` with URL, got `%s`",
                type(file),
            )
            return False

        if file and not mime_type:
            logger.error(
                "You must pass `mime_type` along with `file` field\n"
                "It may be either 'application/zip' or 'application/pdf'"
            )
            return False

        if video and (not isinstance(video, str) or not utils.check_url(video)):
            logger.error(
                "Invalid type for `video`. Expected `str` with URL, got `%s`",
                type(video),
            )
            return False

        if isinstance(audio, str):
            audio = {"url": audio}

        if audio and (
            not isinstance(audio, dict)
            or "url" not in audio
            or not utils.check_url(audio["url"])
        ):
            logger.error(
                "Invalid type for `audio`. Expected `dict` with `url` key, got `%s`",
                type(audio),
            )
            return False

        if location and (
            not isinstance(location, (list, tuple))
            or len(location) != 2
            or not all(isinstance(item, float) for item in location)
        ):
            logger.error(
                (
                    "Invalid type for `location`. Expected `list` or `tuple` with 2"
                    " `float` items, got `%s`"
                ),
                type(location),
            )
            return False

        if [
            photo is not None,
            gif is not None,
            file is not None,
            video is not None,
            audio is not None,
            location is not None,
        ].count(True) > 1:
            logger.error("You passed two or more exclusive parameters simultaneously")
            return False

        reply_markup = self._validate_markup(reply_markup) or []

        if not isinstance(force_me, bool):
            logger.error(
                "Invalid type for `force_me`. Expected `bool`, got `%s`",
                type(force_me),
            )
            return False

        if not isinstance(always_allow, list):
            logger.error(
                "Invalid type for `always_allow`. Expected `list`, got `%s`",
                type(always_allow),
            )
            return False

        if not isinstance(ttl, int) and ttl:
            logger.error("Invalid type for `ttl`. Expected `int`, got `%s`", type(ttl))
            return False

        if isinstance(message, Message) and not silent:
            try:
                status_message = await (
                    message.edit if message.out else message.respond
                )(
                    (
                        utils.get_platform_emoji()
                        if self._client.acbot_me.premium and CUSTOM_EMOJIS
                        else "✍️"
                    )
                    + self.translator.getkey("inline.opening_form"),
                    **({"reply_to": utils.get_topic(message)} if message.out else {}),
                )
            except Exception:
                status_message = None
        else:
            status_message = None

        unit_id = utils.rand(16)

        perms_map = None if manual_security else self._find_caller_sec_map()

        if not reply_markup and not ttl:
            logger.debug("Patching form reply markup with empty data")
            base_reply_markup = copy.deepcopy(reply_markup) or None
            reply_markup = self._validate_markup({"text": "­", "data": "­"})
        else:
            base_reply_markup = Placeholder()

        if (
            not any(
                any("callback" in button or "input" in button for button in row)
                for row in reply_markup
            )
            and not ttl
        ):
            logger.debug(
                "Patching form ttl to 10 minutes, because it doesn't contain any"
                " buttons"
            )
            ttl = 10 * 60

        self._units[unit_id] = {
            "type": "form",
            "text": text,
            **({"rich_html": rich_html} if rich_html is not None else {}),
            "buttons": reply_markup,
            "caller": message,
            "chat": None,
            "message_id": None,
            "top_msg_id": utils.get_topic(message),
            "uid": unit_id,
            "on_unload": on_unload,
            "future": Event(),
            **({"photo": photo} if photo else {}),
            **({"video": video} if video else {}),
            **({"gif": gif} if gif else {}),
            **({"location": location} if location else {}),
            **({"audio": audio} if audio else {}),
            **({"location": location} if location else {}),
            **({"perms_map": perms_map} if perms_map else {}),
            **({"message": message} if isinstance(message, Message) else {}),
            **({"force_me": force_me} if force_me else {}),
            **({"disable_security": disable_security} if disable_security else {}),
            **({"ttl": round(time.time()) + ttl} if ttl else {}),
            **({"always_allow": always_allow} if always_allow else {}),
        }

        async def answer(msg: str):
            nonlocal message
            if isinstance(message, Message):
                await (message.edit if message.out else message.respond)(
                    msg,
                    **({} if message.out else {"reply_to": utils.get_topic(message)}),
                )
            else:
                await self._client.send_message(message, msg)

        try:
            m = await self._invoke_unit(unit_id, message)
        except ChatSendInlineForbiddenError:
            await self._unload_unit(unit_id)
            await answer(self.translator.getkey("inline.inline403"))
            return False
        except Exception:
            logger.exception("Can't send form")

            await self._unload_unit(unit_id)
            await answer(
                self.translator.getkey("inline.invoke_failed_logs").format(
                    utils.escape_html(
                        "\n".join(traceback.format_exc().splitlines()[1:])
                    )
                )
                if self._db.get("acbot.main", "inlinelogs", True)
                else self.translator.getkey("inline.invoke_failed")
            )

            return False

        await self._units[unit_id]["future"].wait()
        del self._units[unit_id]["future"]

        self._units[unit_id]["chat"] = utils.get_chat_id(m)
        self._units[unit_id]["message_id"] = m.id

        if isinstance(message, Message) and message.out:
            await message.delete()

        if status_message and not message.out:
            await status_message.delete()

        inline_message_id = self._units[unit_id]["inline_message_id"]

        msg = InlineMessage(self, unit_id, inline_message_id)

        if not isinstance(base_reply_markup, Placeholder):
            if rich_html is not None and not self._units[unit_id].get("rich_fallback"):
                await self.bot.edit_message_reply_markup(
                    inline_message_id=inline_message_id,
                    reply_markup=self.generate_markup(base_reply_markup),
                )
                self._units[unit_id]["buttons"] = base_reply_markup or []
            else:
                await msg.edit(text, reply_markup=base_reply_markup)

        return msg

    async def _form_inline_handler(self, inline_query: InlineQuery):
        try:
            query = inline_query.query.split()[0]
        except IndexError:
            return

        for unit in self._units.copy().values():
            for button in utils.array_sum(unit.get("buttons", [])):
                if (
                    "_switch_query" in button
                    and "input" in button
                    and button["_switch_query"] == query
                    and inline_query.from_user.id
                    in [self._me]
                    + self._client.dispatcher.security._owner
                    + unit.get("always_allow", [])
                ):
                    await inline_query.answer(
                        [
                            InlineQueryResultArticle(
                                id=utils.rand(20),
                                title=button["input"],
                                description=(
                                    self.translator.getkey("inline.keep_id").format(
                                        random.choice(VERIFICATION_EMOJIES)
                                    )
                                ),
                                input_message_content=InputTextMessageContent(
                                    (
                                        "🔄 <b>Transferring value to"
                                        " userbot...</b>\n<i>This message will be"
                                        " deleted automatically</i>"
                                        if inline_query.from_user.id == self._me
                                        else "🔄 <b>Transferring value to userbot...</b>"
                                    ),
                                    "HTML",
                                    disable_web_page_preview=True,
                                ),
                            )
                        ],
                        cache_time=60,
                    )
                    return

        if (
            inline_query.query not in self._units
            or self._units[inline_query.query]["type"] != "form"
        ):
            return

        form = self._units[inline_query.query]
        if "rich_html" in form:
            try:
                await self.rich.request(
                    "answerInlineQuery", inline_query_id=inline_query.id,
                    results=[{
                        "type": "article", "id": utils.rand(20), "title": "AuthorBot",
                        "input_message_content": {"rich_message": {"html": form["rich_html"]}},
                        "reply_markup": self.generate_markup(form["uid"]),
                    }], cache_time=0, is_personal=True,
                )
                form.pop("rich_fallback", None)
                return
            except Exception:
                # Keep the same controls and classic content on older clients.
                form["rich_fallback"] = True
                logger.debug("Inline Rich Message unavailable; using classic form")
        try:
            if "photo" in form:
                await inline_query.answer(
                    [
                        photo_result(
                            form["photo"],
                            id=utils.rand(20),
                            title="AuthorBot",
                            description="AuthorBot",
                            caption=form.get("text"),
                            parse_mode="HTML",
                            reply_markup=self.generate_markup(
                                form["uid"],
                            ),
                        )
                    ],
                    cache_time=0,
                )
            elif "gif" in form:
                await inline_query.answer(
                    [
                        InlineQueryResultGif(
                            id=utils.rand(20),
                            title="AuthorBot",
                            caption=form.get("text"),
                            parse_mode="HTML",
                            gif_url=form["gif"],
                            thumb_url=(
                                "https://raw.githubusercontent.com/VadymYem/AuthorBot/main/assets/bot_pfp.jpg"
                            ),
                            reply_markup=self.generate_markup(
                                form["uid"],
                            ),
                        )
                    ],
                    cache_time=0,
                )
            elif "video" in form:
                await inline_query.answer(
                    [
                        InlineQueryResultVideo(
                            id=utils.rand(20),
                            title="AuthorBot",
                            description="AuthorBot",
                            caption=form.get("text"),
                            parse_mode="HTML",
                            video_url=form["video"],
                            thumb_url=(
                                "https://raw.githubusercontent.com/VadymYem/AuthorBot/main/assets/bot_pfp.jpg"
                            ),
                            mime_type="video/mp4",
                            reply_markup=self.generate_markup(
                                form["uid"],
                            ),
                        )
                    ],
                    cache_time=0,
                )
            elif "file" in form:
                await inline_query.answer(
                    [
                        InlineQueryResultDocument(
                            id=utils.rand(20),
                            title="AuthorBot",
                            description="AuthorBot",
                            caption=form.get("text"),
                            parse_mode="HTML",
                            document_url=form["file"],
                            mime_type=form["mime_type"],
                            reply_markup=self.generate_markup(
                                form["uid"],
                            ),
                        )
                    ],
                    cache_time=0,
                )
            elif "location" in form:
                await inline_query.answer(
                    [
                        InlineQueryResultLocation(
                            id=utils.rand(20),
                            latitude=form["location"][0],
                            longitude=form["location"][1],
                            title="AuthorBot",
                            reply_markup=self.generate_markup(
                                form["uid"],
                            ),
                        )
                    ],
                    cache_time=0,
                )
            elif "audio" in form:
                await inline_query.answer(
                    [
                        InlineQueryResultAudio(
                            id=utils.rand(20),
                            audio_url=form["audio"]["url"],
                            caption=form.get("text"),
                            parse_mode="HTML",
                            title=form["audio"].get("title", "AuthorBot"),
                            performer=form["audio"].get("performer"),
                            audio_duration=form["audio"].get("duration"),
                            reply_markup=self.generate_markup(
                                form["uid"],
                            ),
                        )
                    ],
                    cache_time=0,
                )
            else:
                await inline_query.answer(
                    [
                        InlineQueryResultArticle(
                            id=utils.rand(20),
                            title="AuthorBot",
                            input_message_content=InputTextMessageContent(
                                form["text"],
                                "HTML",
                                disable_web_page_preview=True,
                            ),
                            reply_markup=self.generate_markup(inline_query.query),
                        )
                    ],
                    cache_time=0,
                )
        except Exception as e:
            if form["uid"] in self._error_events:
                self._error_events[form["uid"]].set()
                self._error_events[form["uid"]] = e
