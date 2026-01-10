import aiohttp
import json
from .. import loader, utils

@loader.tds
class AIContextMod(loader.Module):
    """Аналіз контексту чату за допомогою Gemini AI (Модифікована версія)"""
    
    strings = {
        "name": "AIContext",
        "no_api_key": "<b>⚠️ Помилка: Вкажіть API Key для Gemini у конфігурації (.setconf AIContext api_key <key>)</b>",
        "loading": "<b>⏳ Збираю повідомлення та аналізую (це може зайняти час)...</b>",
        "api_error": "<b>❌ Помилка API:</b> <code>{}</code>",
        "no_messages": "<b>❌ Не вдалося отримати текстові повідомлення для аналізу.</b>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                None,
                lambda: "API ключ для Gemini (отримати на aistudio.google.com)",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "model",
                "gemini-3-flash-preview", 
                lambda: "Модель Gemini (за замовчуванням gemini-3-flash-preview)"
            )
        )

    async def sumcmd(self, message):
        """[кількість] [запит] - Аналіз контексту або Summary (ліміт до 50,000)"""
        args = utils.get_args_raw(message)
        api_key = self.config["api_key"]

        if not api_key:
            await utils.answer(message, self.strings["no_api_key"])
            return

        # Парсинг аргументів (за замовчуванням 500 повідомлень)
        limit = 500
        query = ""
        
        if args:
            parts = args.split(maxsplit=1)
            if parts[0].isdigit():
                limit = int(parts[0])
                if limit > 50000:
                    limit = 50000
                query = parts[1] if len(parts) > 1 else ""
            else:
                query = args

        await utils.answer(message, self.strings["loading"])

        # Отримання історії повідомлень
        messages_history = []
        # Використовуємо raw_text, ігноруємо сервісні повідомлення та порожні тексти
        async for msg in message.client.iter_messages(message.chat_id, limit=limit):
            if msg.raw_text and not msg.action:
                sender = (msg.sender.first_name if msg.sender and hasattr(msg.sender, 'first_name') else "Анонім")
                date = msg.date.strftime("%Y-%m-%d %H:%M")
                messages_history.append(f"{sender} [{date}]: {msg.raw_text}")

        if not messages_history:
            await utils.answer(message, self.strings["no_messages"])
            return

        # Реверсуємо для хронологічного порядку
        messages_history.reverse()
        context_text = "\n".join(messages_history)

        # Формування промпта
        if query:
            prompt = (
                f"Ти професійний асистент. Тобі надано історію переписки.\n"
                f"Твоє завдання: на основі цієї переписки дай відповідь на питання: '{query}'.\n"
                f"Відповідай українською мовою. Якщо відповіді немає в тексті, так і скажи.\n\n"
                f"ІСТОРІЯ ПЕРЕПИСКИ:\n{context_text}"
            )
        else:
            prompt = (
                f"Ти професійний асистент. Тобі надано останні {len(messages_history)} повідомлень з чату.\n"
                f"Зроби детальний підсумок (Summary) цієї переписки українською мовою.\n"
                f"Виділи ключові теми, активних учасників та важливі рішення або висновки.\n\n"
                f"ІСТОРІЯ ПЕРЕПИСКИ:\n{context_text}"
            )

        # Запит до API Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config['model']}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4096,
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    result = await resp.json()
                    
                    if resp.status != 200:
                        error_msg = result.get("error", {}).get("message", "Unknown error")
                        await utils.answer(message, self.strings["api_error"].format(error_msg))
                        return

                    if 'candidates' not in result or not result['candidates']:
                        await utils.answer(message, "<b>❌ AI не зміг згенерувати відповідь (можливо, цензура або пустий контекст).</b>")
                        return

                    ai_response = result['candidates'][0]['content']['parts'][0]['text']
                    
                    header = f"<b>📊 Результат аналізу ({len(messages_history)} повідомлень):</b>\n\n"
                    # Використовуємо ліміт Telegram на довжину повідомлення
                    if len(header + ai_response) > 4096:
                        full_res = header + ai_response
                        for i in range(0, len(full_res), 4000):
                            await utils.answer(message, full_res[i:i+4000])
                    else:
                        await utils.answer(message, f"{header}{ai_response}")

        except Exception as e:
            await utils.answer(message, self.strings["api_error"].format(str(e)))