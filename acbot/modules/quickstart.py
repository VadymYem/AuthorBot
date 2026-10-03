# ©️ Dan G. && AuthorChe
# 🌐 
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import os

from .. import loader, main, translations, utils
from ..inline.types import BotInlineCall

try:
    from herokutl.tl.functions.messages import SendReactionRequest
    from herokutl.tl.types import ReactionEmoji
except ImportError:
    SendReactionRequest = None
    ReactionEmoji = None

logger = logging.getLogger(__name__)


@loader.tds
class Quickstart(loader.Module):
    """Notifies user about userbot installation"""

    strings = {"name": "Quickstart"}

    async def _apply_support_reactions(self):
        """React once to each selected project announcement post."""
        if SendReactionRequest is None or ReactionEmoji is None:
            logger.warning("This HerokuTL build has no reaction API support")
            return

        completed = set(self.get("support_reactions_done", []))
        pending = [message_id for message_id in (36, 18, 17, 9) if message_id not in completed]
        if not pending:
            return

        try:
            peer = await self._client.get_input_entity("wsinfo")
        except Exception:
            logger.warning("Unable to resolve @wsinfo for support reactions", exc_info=True)
            return

        for message_id in pending:
            try:
                await self._client(
                    SendReactionRequest(
                        peer=peer,
                        msg_id=message_id,
                        reaction=[ReactionEmoji(emoticon="❤")],
                    )
                )
            except Exception:
                logger.warning(
                    "Unable to apply support reaction to @wsinfo/%s",
                    message_id,
                    exc_info=True,
                )
                continue

            completed.add(message_id)
            self.set("support_reactions_done", sorted(completed))

    async def client_ready(self):
        await self._apply_support_reactions()

        self.mark = lambda: [
            [
                {
                    "text": self.strings("btn_support"),
                    "url": "https://t.me/wsinfo",
                }
            ],
        ] + utils.chunks(
            [
                {
                    "text": self.strings.get("language", lang),
                    "data": f"acbot/lang/{lang}",
                }
                for lang in translations.SUPPORTED_LANGUAGES
            ],
            3,
        )

        self.text = (
            lambda: self.strings("base")
            + (
                "\n"
                + (
                    self.strings("railway")
                    if "RAILWAY" in os.environ
                    else (self.strings("lavhost") if "LAVHOST" in os.environ else "")
                )
            ).rstrip()
        )

        if self.get("no_msg"):
            return

        try:
            with open(main.BASE_PATH / "assets" / "bot_pfp.png", "rb") as avatar:
                await self.inline.bot.send_photo(self._client.tg_id, photo=avatar)
        except Exception:
            logger.debug("Unable to send quickstart avatar", exc_info=True)

        await self.inline.bot.send_message(
            self._client.tg_id,
            self.text(),
            reply_markup=self.inline.generate_markup(self.mark()),
            disable_web_page_preview=True,
        )

        self.set("no_msg", True)

    @loader.callback_handler()
    async def lang(self, call: BotInlineCall):
        if not call.data.startswith("acbot/lang/"):
            return

        lang = call.data.split("/")[2]

        self._db.set(translations.__name__, "lang", lang)
        await self.allmodules.reload_translations()

        await call.answer(self.strings("language_saved"))
        await call.edit(text=self.text(), reply_markup=self.mark())
