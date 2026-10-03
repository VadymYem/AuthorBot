# ©️ Dan G. && AuthorChe
# 🌐 
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging

from .. import loader, translations, utils
from ..branding import BOT_PHOTO
from ..inline.types import BotInlineCall
from ..public_pages import rich_page, fallback_page, text as page_text

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
        skipped = set(self.get("support_reactions_skipped", []))
        pending = [message_id for message_id in (36, 18, 17, 9) if message_id not in completed | skipped]
        if not pending:
            return

        try:
            peer = await self._client.get_input_entity("wsinfo")
        except Exception as exc:
            logger.warning("Support reactions unavailable (%s)", type(exc).__name__)
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
            except Exception as exc:
                if "CUSTOM_REACTIONS_TOO_MANY" in str(exc):
                    skipped.add(message_id)
                    self.set("support_reactions_skipped", sorted(skipped))
                    logger.debug("Telegram reaction limit reached for @wsinfo/%s; skipping", message_id)
                else:
                    logger.warning("Support reaction to @wsinfo/%s skipped (%s)", message_id, type(exc).__name__)
                continue

            completed.add(message_id)
            self.set("support_reactions_done", sorted(completed))

    async def client_ready(self):
        await self._apply_support_reactions()

        self.mark = lambda: [
            [
                {
                    "text": "AuthorChe · Telegram",
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

        self.text = lambda: fallback_page("welcome", self._language(), prefix=self.get_prefix())

        if self.get("no_msg"):
            return

        await self._send_welcome()

        self.set("no_msg", True)

    def _language(self):
        selected = self._db.get(translations.__name__, "lang", "en").split()
        return next((translations.normalize_language(lang) for lang in selected
                     if translations.normalize_language(lang) in translations.SUPPORTED_LANGUAGES), "en")

    async def _send_welcome(self):
        markup = self.inline.generate_markup(self.mark())
        try:
            await self.inline.rich.send(
                self._client.tg_id,
                html=rich_page("welcome", self._language(), prefix=self.get_prefix()),
                media=[{"id": "bot_artwork", "media": {"type": "photo", "media": "attach://bot_artwork"}}],
                files={"bot_artwork": BOT_PHOTO}, reply_markup=markup,
            )
            return
        except Exception:
            logger.debug("Using classic onboarding for this Bot API/client")
        await self.inline.bot.send_message(
            self._client.tg_id, self.text(), reply_markup=markup,
            disable_web_page_preview=True,
        )

    @loader.callback_handler()
    async def lang(self, call: BotInlineCall):
        if not call.data.startswith("acbot/lang/"):
            return

        lang = translations.normalize_language(call.data.split("/")[2])
        if lang not in translations.SUPPORTED_LANGUAGES or call.from_user.id != self._client.tg_id:
            return

        self._db.set(translations.__name__, "lang", lang)
        await self.allmodules.reload_translations()

        await call.answer(page_text("language_saved", lang))
        await self._send_welcome()
        # Send first: if delivery fails, the existing language picker stays usable.
        try:
            await self.inline.bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            logger.debug("Previous welcome message could not be removed")
