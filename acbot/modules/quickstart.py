
#              © Copyright 2022
#           https://t.me/authorche
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import os
from random import choice

from .. import loader, translations
from ..inline.types import BotInlineCall

imgs = [
    "https://i.gifer.com/GmUB.gif",
    "https://i.gifer.com/Afdn.gif",
    "https://i.gifer.com/3uvT.gif",
    "https://i.gifer.com/2qQQ.gif",
    "https://i.gifer.com/Lym6.gif",
    "https://i.gifer.com/IjT4.gif",
    "https://i.gifer.com/A9H.gif",
]

TEXT = """🇬🇧 <b>Hello.</b> You've just installed <b>AuthorChe's</b> userbot.

📼 <b>You can find and install modules using @hikkamods_bot or @ftg2bot. Simply enter your search query and click ⛩ Install on needed module</b>

💁‍♀️ <b>Quickstart:</b>

1️⃣ <b>Type </b><code>.help</code> <b>to see modules list</b>
2️⃣ <b>Type </b><code>.help &lt;ModuleName/command&gt;</code> <b>to see help of module ModuleName</b>
3️⃣ <b>Type </b><code>.dlmod &lt;link&gt;</code> <b>to load module from link</b>
4️⃣ <b>Type </b><code>.loadmod</code> <b>with reply to file to install module from it</b>
5️⃣ <b>Type </b><code>.unloadmod &lt;ModuleName&gt;</code> <b>to unload module ModuleName</b>

💡 <b>AuthorBot supports modules from Hikka, Friendly-Telegram and GeekTG, as well as its own ones.</b>
"""


TEXT_UA = """🇺🇦 <b>Привiт.</b> Твiй юзербот <b>AuthorChe's</b> встановлено.

📼 <b>Ти можеш шукати й встановлювати модулі через @hikkamods_bot або @ftg2bot. Просто введи пошуковий запит й натисни ⛩ Install на потрібному модулі або скористайся `.dlmod`</b>

💁‍♀️ <b>Швидкий гайд:</b>

1️⃣ <b>Напиши </b><code>.help</code> <b>щоб побачити список модулів</b>
2️⃣ <b>Напиши </b><code>.help &lt;Назва модуля/команда&gt;</code> <b>щоб побачити опис модуля</b>
3️⃣ <b>Напиши </b><code>.dlmod &lt;посилання&gt;</code> <b>щоб завантажити модуль з посилання</b>
4️⃣ <b>Напиши </b><code>.loadmod</code> <b>в відповідь на файл, щоб завантажити модуль з нього</b>
5️⃣ <b>Напиши </b><code>.unloadmod &lt;Назва модуля&gt;</code> <b>щоб видалити модуль</b>

💡 <b>AuthorBot підтримує модулі з Hikka, Friendly-Telegram и GeekTG, а також свої власні.</b>
"""

if "OKTETO" in os.environ:
    TEXT += (
        "☁️ <b>Your userbot is installed on Okteto</b>. You will get notifications from"
        " @WebpageBot. Do not block him."
    )
    TEXT_UA += (
        "☁️ <b>Твiй юзербот встановлено на Okteto</b>. Ти будеш отримувати повідомлення від"
        " @WebpageBot. Не блокуй його."
    )

if "RAILWAY" in os.environ:
    TEXT += (
        "🚂 <b>Your userbot is installed on Railway</b>. This platform has only <b>500"
        " free hours per month</b>. Once this limit is reached, your <b>acbot will be"
        " frozen</b>. Next month <b>you will need to go to https://railway.app and"
        " restart it</b>."
    )
    TEXT_UA += (
        "🚂 <b>Твiй юзербот встановлено на Railway</b>. На цій платформі ти отримуєш"
        " тільки <b>500 безкоштовних годин в місяц</b>. Коли ліміт буде досягнуто, твій"
        " <b>юзербот буде заморожено</b>. В наступному місяці <b>ти повинен будеш"
        " перейти на https://railway.app и перезапустити його</b>."
    )


@loader.tds
class QuickstartMod(loader.Module):
    """Notifies user about userbot installation"""

    strings = {"name": "Quickstart"}

    async def client_ready(self):
        if self._db.get("acbot", "disable_quickstart", False):
            raise loader.SelfUnload

        self.mark = (
            lambda lang: [
                [{"text": "AuthorChannel", "url": "https://t.me/authorche"}],
                [
                    {
                        "text": "🇺🇦 Змінити мову",
                        "callback": self._change_lang,
                        "args": ("ua",),
                    }
                ],
            ]
            if lang == "en"
            else [
                [{"text": "AuthorChannel", "url": "https://t.me/AuthorChe"}],
                [
                    {
                        "text": "🇬🇧 Switch language",
                        "callback": self._change_lang,
                        "args": ("en",),
                    }
                ],
            ]
        )

        await self.inline.bot.send_animation(self._client.tg_id, animation=choice(imgs))
        await self.inline.bot.send_message(
            self._client.tg_id,
            TEXT,
            reply_markup=self.inline.generate_markup(self.mark("en")),
            disable_web_page_preview=True,
        )

        self._db.set("acbot", "disable_quickstart", True)

    async def _change_lang(self, call: BotInlineCall, lang: str):
        if lang == "ua":
            self._db.set(translations.__name__, "lang", "ua")
            await self.translator.init()
            await call.answer("🇺🇦 Мову збережено!")
            await call.edit(text=TEXT_UA, reply_markup=self.mark("ua"))
        elif lang == "en":
            self._db.set(translations.__name__, "lang", "en")
            await self.translator.init()
            await call.answer("🇬🇧 Language saved!")
            await call.edit(text=TEXT, reply_markup=self.mark("en"))
