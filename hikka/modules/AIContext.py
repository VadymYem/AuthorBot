import aiohttp
import json
from .. import loader, utils

@loader.tds
class AIContextMod(loader.Module):
    """Модуль для аналізу контексту чату за допомогою Gemini AI"""
    
    strings = {
        "name": "AIContext",
        "no_api_key": "<b>⚠️ Помилка: Вкажіть API Key для Gemini у конфігурації (.setconf AIContext api_key <key>)</b>",
        "loading": "<b>⏳ Аналізую повідомлення...</b>",
        "api_error": "<b>❌ Помилка API:</b> <code>{}</code>",
        "no_messages": "<b>❌ Не вдалося отримати повідомлення для аналізу.</b>"
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
                "gemini-1.5-flash", 
                lambda: "Модель Gemini (за замовчуванням gemini-1.5-flash, бо gemini-3 ще не існує)"
            )
        )

    async def sumcmd(self, message):
        """[кількість] [запит] - Робить Summary або шукає відповідь у контексті"""
        args = utils.get_args_raw(message)
        api_key = self.config["api_key"]

        if not api_key:
            await utils.answer(message, self.strings["no_api_key"])
            return

        # Парсинг аргументів
        limit = 50
        query = ""
        
        if args:
            parts = args.split(maxsplit=1)
            if parts[0].isdigit():
                limit = int(parts[0])
                query = parts[1] if len(parts) > 1 else ""
            else:
                query = args

        await utils.answer(message, self.strings["loading"])

        # Отримання історії повідомлень
        messages_history = []
        async for msg in message.client.iter_messages(message.chat_id, limit=limit):
            if msg.text:
                sender = (msg.sender.first_name if msg.sender and msg.sender.first_name else "Анонім")
                date = msg.date.strftime("%Y-%m-%d %H:%M")
                messages_history.append(f"{sender} [{date}]: {msg.text}")

        if not messages_history:
            await utils.answer(message, self.strings["no_messages"])
            return

        # Реверсуємо, щоб був хронологічний порядок
        messages_history.reverse()
        context_text = "\n".join(messages_history)

        # Формування промпта
        if query:
            prompt = (
                f"Ти професійний асистент. Тобі надано історію переписки нижче.\n"
                f"Твоє завдання: на основі цієї переписки дай відповідь на питання: '{query}'.\n"
                f"Відповідай українською мовою. Якщо відповіді немає в тексті, так і скажи.\n\n"
                f"ІСТОРІЯ ПЕРЕПИСКИ:\n{context_text}"
            )
        else:
            prompt = (
                f"Ти професійний асистент. Тобі надано останні {limit} повідомлень з чату.\n"
                f"Зроби короткий, але інформативний підсумок (Summary) цієї переписки українською мовою.\n"
                f"Виділи основні теми обговорення та висновки, якщо вони є.\n\n"
                f"ІСТОРІЯ ПЕРЕПИСКИ:\n{context_text}"
            )

        # Запит до API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config['model']}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
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

                    ai_response = result['candidates'][0]['content']['parts'][0]['text']
                    
                    header = "<b>📊 Результат аналізу:</b>\n\n"
                    await utils.answer(message, f"{header}{ai_response}")

        except Exception as e:
            await utils.answer(message, self.strings["api_error"].format(str(e)))