# ©️ Dan G. && AuthorChe
# 🌐 
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html
import asyncio
import logging
from ..branding import bot_photo

from .. import loader, utils
from ..inline.types import BotInlineMessage, InlineCall
from ..types import Message

logger = logging.getLogger(__name__)


PRESETS = {'fun': ['https://raw.githubusercontent.com/coddrago/modules/main/dice.py',
         'https://raw.githubusercontent.com/coddrago/modules/main/loli.py',
         'https://raw.githubusercontent.com/coddrago/modules/main/DoxTool.py',
         'https://raw.githubusercontent.com/coddrago/modules/main/randomizer.py'],
 'chat': ['https://raw.githubusercontent.com/coddrago/modules/main/id.py',
          'https://raw.githubusercontent.com/coddrago/modules/main/clickon.py'],
 'service': ['https://raw.githubusercontent.com/coddrago/modules/main/modlist.py']}


@loader.tds
class Presets(loader.Module):
    """Suggests for users a packs of modules to load"""

    strings = {"name": "Presets"}

    async def client_ready(self):
        self._markup = utils.chunks(
            [
                {
                    "text": self.strings(f"_{preset}_title"),
                    "callback": self._preset,
                    "args": (preset,),
                }
                for preset in PRESETS
            ],
            1,
        )

        if self.get("sent"):
            return

        await self._menu()
        self.set("sent", True)

    async def _menu(self):
        await self.inline.bot.send_photo(
            self._client.tg_id,
            bot_photo(),
            caption=self.strings('welcome'),
            reply_markup=self.inline.generate_markup(self._markup),
        )

    async def _back(self, call: InlineCall):
        await call.edit(self.strings("welcome"), reply_markup=self._markup)

    async def _install(self, call: InlineCall, preset: str):
        await call.delete()
        m = await self._client.send_message(
            self.inline.bot_id,
            self.strings("installing").format(preset),
        )
        failed = []
        for i, module in enumerate(PRESETS[preset], start=1):
            await m.edit(
                self.strings("installing_module").format(
                    preset,
                    i,
                    len(PRESETS[preset]),
                    module,
                )
            )
            try:
                if not await self.lookup("loader").download_and_install(module, None):
                    failed.append(module)
            except Exception:
                logger.exception("Failed to install module %s", module)
                failed.append(module)

            await asyncio.sleep(1)

        if self.lookup("loader").fully_loaded:
            self.lookup("loader").update_modules_in_db()

        if failed:
            await m.edit(
                "<b>Не вдалося встановити модулі:</b>\n"
                + "\n".join(f"<code>{utils.escape_html(link)}</code>" for link in failed)
            )
        else:
            await m.edit(self.strings("installed").format(preset))
        await self._menu()

    def _is_installed(self, link: str) -> bool:
        return any(
            link.strip().lower() == installed.strip().lower()
            for installed in self.lookup("loader").get("loaded_modules", {}).values()
        )

    async def _preset(self, call: InlineCall, preset: str):
        await call.edit(
            self.strings("preset").format(
                self.strings(f"_{preset}_title"),
                self.strings(f"_{preset}_desc"),
                "\n".join(
                    map(
                        lambda x: x[0],
                        sorted(
                            [
                                (
                                    "{} <b>{}</b>".format(
                                        (
                                            self.strings("already_installed")
                                            if self._is_installed(link)
                                            else "▫️"
                                        ),
                                        link.rsplit("/", maxsplit=1)[1].split(".")[0],
                                    ),
                                    int(self._is_installed(link)),
                                )
                                for link in PRESETS[preset]
                            ],
                            key=lambda x: x[1],
                            reverse=True,
                        ),
                    )
                ),
            ),
            reply_markup=[
                {"text": self.strings("back"), "callback": self._back},
                {
                    "text": self.strings("install"),
                    "callback": self._install,
                    "args": (preset,),
                },
            ],
        )

    async def aiogram_watcher(self, message: BotInlineMessage):
        if message.text != "/presets" or message.from_user.id != self._client.tg_id:
            return

        await self._menu()

    @loader.command()
    async def presets(self, message: Message):
        await self.inline.form(
            message=message,
            photo=await self.inline.brand_photo(),
            text=self.strings('welcome').replace('/presets', self.get_prefix() + 'presets'),
            reply_markup=self._markup,
        )
