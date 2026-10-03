# AuthorChe
# 🌐 
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import abc
import time

from aiogram.types import Message as AiogramMessage, InlineKeyboardMarkup, InlineKeyboardButton
from telethon.utils import get_display_name

from .. import loader, utils
from ..inline.types import InlineCall

@loader.tds
class MenuBotMod(loader.Module):
    """Simple menu for bot"""

    metaclass = abc.ABCMeta

    strings = {
        "name": "ТестBot",
        "/donate": (
            "<i>✌️So you want to donate?\nAmazing!\n\nYou can send money to my cards(UA)</i>:\n"
            "<b>Privat24💸</b> - <code>5168745150640644\n</code>\n"
            "<i>Or my crypto wallets👛</i>:\n\n"
            "<b>•🪙 BTC</b>:\n<code>123MgBkkpu6XwrU53SvrBxiW9useRSt6qR\n</code>\n"
            "<b>•💎 TON</b>:\n<code>UQDicYt03peG8l0CBCKW2YQJ914YoKkzObWFbbIIdUlqnpNJ\n</code>\n"
            "<b>•💲USDT(TON): \n</b><code>UQBqKU8fvbZVZJvyAw85wQP88O0sTzFkBxW1lfbht9hGayBK</code> \n"
            "or\n<b>•💲USDT(TRX): \n</b><code>TXkiayvYBwyuX7r9dj5NvEfdF5FCJbu5kb</code>\n\n"
            "<b>❤️Donate via xRocket🚀 - /xrocket\n🙏 authorche.top/sup - всі способи підтримки.\n\n"
            "<i>🙃It's a trifle for you, but I'm pleased, so I thank you for your support!</i></b>"
        ),
        "/author": (
            "<b>😎Власником боту є @Author_Che.</b> Бот є <i>повністю безкоштовним та не містить жодної реклами.</i> "
            "Ціллю створення є бажання спростити користування месенджером Telegram. \nТакож є і інші проекти: "
            "@wsinfo. <b>\n\n<i>Ви можете підтримати проект</i></b> — /donate"
        ),
        "/bots1": (
            "<i>Наразі працюють лише два боти😢:\n</i>@authorche_nice_bot та @vyfb_bot.\n\n"
            "🥺 Допоможи проекту відновити роботу решти ботів. Орендування серверів дуже недешева річ.\n"
            "<b>Підтримай проект донатом: /donate</b>\n\n"
            "<i>👀 Також Автор пише ботів(only python already) та створює веб-сайти[Портфоліо](html/css/js) на замовлення. \nЯкщо я тебе зацікавив, то "
            "можеш звернутися до нього через: @vyfb_bot або authorche.top/dev\n</i>"
        ),
        "/bots": (
            "<b>Список безкоштовних ботів:</b>\n"
            "@authorche_nice_bot - HandWriter бот,\n"
            "@emails_tgbot - простий та зручний поштовий клієнт в телеграм,\n"
            "@authorcloud_bot - Безкоштовний файлообмінник. Хмарне сховище в телеграм.\n"
            "@ac_moder_bot - Модератор чатів. Ваш помічник в модерації груп\n"
            "@vyfb_bot - бот зворотнього зв'язку з Автором.\n\n"
            "<b>Список всих проектів:</b> @wsinfo\n"
            "🥺Допоможи проекту підтримувати роботу та обслуговування ботів. Орендування серверів дуже недешева річ.\n"
            "<b>Підтримай проект донатом: /donate</b>\n\n"
            "<i>👀Також Автор пише простих ботів(only python) та створює веб-сайти[портфоліо](html/css/js) на замовлення. \nЯкщо я тебе зацікавив, то "
            "можеш звернутися до нього через: @vyfb_bot\n</i>"
        ),
        "/main": (
            "<b>Якщо чесно, я тебе не розумію😅.</b>\nСкористайся однією з команд в меню /menu"
        ),
        "/menu": (
            "✌️<b>Привіт, вітаю в меню\n"
            "Команди які ви можете використовувати</b>:\n"
            "/author — <i>Посилання на власника боту😎</i>\n"
            "/donate — <b><i>Donate❤️</i></b>\n"
            "/bots — <i>Список інших ботів від Автора👀</i>\n"
            "/menu — <i>Переглянути функціонал бота📝</i>\n\n"
        ),
        "start_acbot_init": "🔄 Бот успішно перезапущено!",
    }

    async def client_ready(self):
        self._name = utils.escape_html(get_display_name(self._client.acbot_me))
        self.doc = "Menu for bot\n"

    async def aiogram_watcher(self, message: AiogramMessage):
        # Обработка команды перезапуска
        if message.text.startswith("/start acbot init"):
            await message.answer(self.strings["start_acbot_init"])
            return

        # Основные команды
        if message.text == "/donate":
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("CryptoBot 💳", url="http://t.me/send?start=IVzEgNnRlefO")
            )
            await message.answer(
                self.strings["/donate"].format(self._name),
                reply_markup=keyboard
            )
        elif message.text == "/menu":
            await message.answer(self.strings["/menu"])
        elif message.text == "/bots":
            await message.answer(self.strings["/bots"])
        elif message.text == "/author":
            await message.answer(self.strings["/author"])
        elif message.text == "/xrocket":
            xrocket_keyboard = InlineKeyboardMarkup(row_width=1)
            xrocket_keyboard.add(
                InlineKeyboardButton("TON", url="https://t.me/xrocket?start=inv_4Wfq3fmqadtyNEP"),
                InlineKeyboardButton("USDT", url="https://t.me/xrocket?start=inv_i8nnYkalSWY7n8i"),
                InlineKeyboardButton("TRX", url="https://t.me/xrocket?start=inv_QOTWjNQHWLPkfrJ"),
                InlineKeyboardButton("BTC", url="https://t.me/xrocket?start=inv_QYFKjAKihGWpTW1")
            )
            await message.answer(
                "Способи оплати через xRocket🚀",
                reply_markup=xrocket_keyboard
            )
        elif message.text:
            await message.answer(self.strings["/main"])
