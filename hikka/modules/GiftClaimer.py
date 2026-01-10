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
        "config_api_key": "API ключ для Gemini (вимоги розробки)",
        "enabled": "✅ <b>Авто-збір увімкнено:</b> <code>{}</code>",
        "claimed": "🎁 <b>Подарунок було натиснуто у каналі!</b>",
        "status": "ℹ️ <b>Статус модуля:</b>\nКаннал: <code>{}</code>\nАктивний: <code>{}</code>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "target_channel",
                "TrueMafia",
                lambda: self.strings["config_channel"],
            ),
            loader.ConfigValue(
                "api_key",
                "",
                lambda: self.strings["config_api_key"],
            ),
            loader.ConfigValue(
                "enabled",
                True,
                lambda: "Увімкнути/Вимкнути автоматичний збір",
            ),
            loader.ConfigValue(
                "gemini_model",
                "gemini-1.5-flash-preview",
                lambda: "Актуальна модель Gemini для аналізу (за вимогами)",
            ),
        )

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
        """Спостерігач за новими повідомленнями"""
        if not self.config["enabled"]:
            return

        if not message or not message.chat:
            return

        # Отримуємо юзернейм або ID чату
        target = str(self.config["target_channel"]).replace("@", "").lower()
        chat_username = (message.chat.username or "").lower()
        chat_id = str(message.chat_id)

        # Перевірка чи повідомлення з потрібного каналу
        if chat_username == target or chat_id == target:
            # Перевіряємо наявність кнопок у повідомленні
            if hasattr(message, "reply_markup") and message.reply_markup:
                try:
                    # Затримка для запобігання флуду та підозрілої активності
                    await asyncio.sleep(0.5)
                    
                    # Намагаємося натиснути на першу кнопку в повідомленні
                    # (зазвичай подарунки мають одну головну кнопку)
                    await message.click(0)
                    
                    # Логуємо успішну спробу
                    logger.info(f"Спроба забрати подарунок у чаті {chat_id}")
                    
                except Exception as e:
                    logger.error(f"Помилка при натисканні кнопки: {e}")

    async def geministatcmd(self, message):
        """Команда для перевірки конфігурації Gemini (згідно з правилом 9)"""
        api_key_status = "Встановлено" if self.config["api_key"] else "Відсутній"
        model = self.config["gemini_model"]
        await utils.answer(
            message, 
            f"🤖 <b>Gemini Config:</b>\nМодель: <code>{model}</code>\nAPI Key: <code>{api_key_status}</code>"
        )