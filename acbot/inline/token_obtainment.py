import asyncio
import logging
import re

from herokutl.errors.rpcerrorlist import YouBlockedUserError
from herokutl.tl.functions.contacts import UnblockRequest

from .. import utils
from .._internal import fw_protect
from .types import InlineUnit

logger = logging.getLogger(__name__)


class TokenObtainment(InlineUnit):
    _BOT_TOKEN_RE = re.compile(r"\b\d{5,12}:[A-Za-z0-9_-]{30,}\b")
    _MANAGED_BOT_RE = re.compile(
        r"@(?:ac_[0-9A-Za-z]{6}_ubot|author_[0-9A-Za-z]{6}_off_AC_bot)$",
        re.IGNORECASE,
    )

    @staticmethod
    def _safe_botfather_log(direction: str, message) -> None:
        text = getattr(message, "raw_text", "") or ""
        logger.debug("%s BotFather response (%d chars)", direction, len(text))

    @classmethod
    def _extract_token(cls, message) -> str:
        text = getattr(message, "raw_text", "") or ""
        match = cls._BOT_TOKEN_RE.search(text)
        if not match:
            raise RuntimeError("BotFather response did not contain a valid bot token")
        return match.group(0)

    async def _create_bot(self):
        logger.info("User doesn't have bot, attempting creating new one")
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            await fw_protect()
            m = await conv.send_message("/newbot")
            r = await conv.get_response()

            self._safe_botfather_log("received", r)

            if "20" in r.raw_text:
                return False

            await fw_protect()

            await m.delete()
            await r.delete()

            if self._db.get("acbot.inline", "custom_bot", False):
                username = self._db.get("acbot.inline", "custom_bot").strip("@")
                username = f"@{username}"
                try:
                    await self._client.get_entity(username)
                except ValueError:
                    pass
                else:
                    uid = utils.rand(6)
                    username = f"@author_{uid}_off_AC_bot"
            else:
                uid = utils.rand(6)
                username = f"@author_{uid}_off_AC_bot"

            for msg in [
                "Author Bot off",
                username,
                "/setuserpic",
                username,
            ]:
                await fw_protect()
                m = await conv.send_message(msg)
                r = await conv.get_response()

                self._safe_botfather_log("received", r)

                await fw_protect()
                await m.delete()
                await r.delete()

            try:
                await fw_protect()
                from .. import main

                m = await conv.send_file(main.BASE_PATH / "assets" / "bot_pfp.jpg")
                r = await conv.get_response()

                logger.debug(">> <Photo>")
                self._safe_botfather_log("received", r)
            except Exception:
                await fw_protect()
                m = await conv.send_message("/cancel")
                r = await conv.get_response()

                self._safe_botfather_log("received", r)

            await fw_protect()

            await m.delete()
            await r.delete()

        return await self._assert_token(False)

    async def _assert_token(
        self,
        create_new_if_needed: bool = True,
        revoke_token: bool = False,
    ) -> bool:
        if self._token:
            return True

        logger.info("Bot token not found in db, attempting search in BotFather")

        if not self._db.get(__name__, "no_mute", False):
            await utils.dnd(
                self._client,
                await self._client.get_entity("@BotFather"),
                True,
            )
            self._db.set(__name__, "no_mute", True)

        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                await fw_protect()
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                await fw_protect()
                m = await conv.send_message("/token")

            r = await conv.get_response()

            logger.debug("Sent BotFather command")
            self._safe_botfather_log("received", r)

            await fw_protect()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                await conv.cancel_all()

                return await self._create_bot() if create_new_if_needed else False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if self._db.get(
                        "acbot.inline", "custom_bot", False
                    ) and self._db.get(
                        "acbot.inline", "custom_bot", False
                    ) != button.text.strip("@"):
                        continue

                    if not self._db.get(
                        "acbot.inline",
                        "custom_bot",
                        False,
                    ) and not self._MANAGED_BOT_RE.search(button.text):
                        continue

                    await fw_protect()

                    m = await conv.send_message(button.text)
                    r = await conv.get_response()

                    self._safe_botfather_log("received", r)

                    if revoke_token:
                        await fw_protect()
                        await m.delete()
                        await r.delete()

                        await fw_protect()

                        m = await conv.send_message("/revoke")
                        r = await conv.get_response()

                        self._safe_botfather_log("received", r)

                        await fw_protect()

                        await m.delete()
                        await r.delete()

                        await fw_protect()

                        m = await conv.send_message(button.text)
                        r = await conv.get_response()

                        self._safe_botfather_log("received", r)

                    token = self._extract_token(r)

                    self._db.set("acbot.inline", "bot_token", token)
                    self._token = token

                    await fw_protect()

                    await m.delete()
                    await r.delete()

                    for msg in [
                        "/setinline",
                        button.text,
                        "🔎 AuthorChe",
                        "/setinlinefeedback",
                        button.text,
                        "Enabled",
                        "/setuserpic",
                        button.text,
                    ]:
                        await fw_protect()
                        m = await conv.send_message(msg)
                        r = await conv.get_response()

                        self._safe_botfather_log("received", r)

                        await fw_protect()

                        await m.delete()
                        await r.delete()

                    try:
                        await fw_protect()
                        from .. import main

                        m = await conv.send_file(
                            main.BASE_PATH / "assets" / "bot_pfp.jpg"
                        )
                        r = await conv.get_response()

                        logger.debug(">> <Photo>")
                        self._safe_botfather_log("received", r)
                    except Exception:
                        await fw_protect()
                        m = await conv.send_message("/cancel")
                        r = await conv.get_response()

                        self._safe_botfather_log("received", r)

                    await fw_protect()

                    await m.delete()
                    await r.delete()

                    return True

        return await self._create_bot() if create_new_if_needed else False

    async def _reassert_token(self):
        is_token_asserted = await self._assert_token(revoke_token=True)
        if not is_token_asserted:
            self.init_complete = False
        else:
            await self.register_manager(ignore_token_checks=True)

    async def _dp_revoke_token(self, already_initialised: bool = True):
        if already_initialised:
            await self._stop()
            logger.error("Got polling conflict. Attempting token revocation...")

        self._db.set("acbot.inline", "bot_token", None)
        self._token = None
        if already_initialised:
            asyncio.ensure_future(self._reassert_token())
        else:
            return await self._reassert_token()
