#meta developer: AuthorChe (@wsinfo)
# t.me/wsinfo

from .. import loader, utils
import asyncio
import logging

logger = logging.getLogger(__name__)

@loader.tds
class GiftClaimerMod(loader.Module):
    """Модуль для автоматичного збору подарунків з вказаного Телеграм-каналу через кнопки"""
    
    strings = {
        "name": "GiftClaimer",
        "config_channel": "Юзернейм або ID каналу для моніторингу (без @)",
        "enabled": "✅ <b>Авто-збір увімкнено:</b> <code>{}</code>",
        "claimed": "🎁 <b>Спроба натиснути на кнопку подарунка!</b>",
        "status": "ℹ️ <b>Статус модуля:</b>\nКанал: <code>{}</code>\nАктивний: <code>{}</code>",
        "set_channel": "✅ <b>Канал для моніторингу змінено на:</b> <code>{}</code>",
        "no_args": "⚠️ <b>Вкажіть юзернейм каналу після команди!</b>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "target_channel",
                "mafiauachannel",
                lambda: self.strings["config_channel"],
            ),
            loader.ConfigValue(
                "enabled",
                True,
                lambda: "Увімкнути/Вимкнути автоматичний збір",
            ),
        )

    async def giftsetcmd(self, message):
        """Вказати юзернейм каналу для збору подарунків"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["no_args"])
            return
        
        channel = args.replace("@", "").strip()
        self.config["target_channel"] = channel
        await utils.answer(message, self.strings["set_channel"].format(channel))

    async def giftclaimcmd(self, message):
        """Перевірити статус налаштувань авто-збору"""
        status = "ТАК" if self.config["enabled"] else "НІ"
        channel = self.config["target_channel"]
        await utils.answer(message, self.strings["status"].format(channel, status))

    async def giftclaimtogglecmd(self, message):
        """Увімкнути або вимкнути авто-збір"""
        self.config["enabled"] = not self.config["enabled"]
        await utils.answer(message, self.strings["enabled"].format(self.config["enabled"]))

    async def watcher(self, message):
        """Спостерігач за новими повідомленнями в каналі"""
        if not self.config["enabled"]:
            return

        if not message or not message.chat:
            return

        # Отримуємо цільовий канал з конфігу
        target = str(self.config["target_channel"]).replace("@", "").lower()
        
        # Перевіряємо юзернейм та ID
        chat_username = (message.chat.username or "").lower()
        chat_id = str(message.chat_id)

        if chat_username == target or chat_id == target:
            # Якщо повідомлення має кнопки
            if hasattr(message, "reply_markup") and message.reply_markup:
                try:
                    # Затримка 0.5с для безпеки від анти-флуду
                    await asyncio.sleep(0.5)
                    
                    # Натискаємо на першу кнопку (index 0)
                    await message.click(0)
                    
                    logger.info(f"GiftClaimer: Кнопку натиснуто в каналі {target}")
                except Exception as e:
                    logger.error(f"GiftClaimer Error: {e}")