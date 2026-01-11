#meta developer: chernykh-mykhailo (@Div4unka_z_kare)
# t.me/myshcode_ai

import aiohttp
import json
import asyncio
import re
from .. import loader, utils

@loader.tds
class AIContextMod(loader.Module):
    """Аналіз контексту чату за допомогою Gemini AI з виправленим форматуванням"""
    
    strings = {
        "name": "AIContext",
        "no_api_key": "<b>⚠️ Помилка: Вкажіть API Key для Gemini у конфігурації (.setconf AIContext api_key <key>)</b>",
        "loading": "<b>⏳ Збираю повідомлення та аналізую (це може зайняти час)...</b>",
        "api_error": "<b>❌ Помилка API:</b> <code>{}</code>",
        "no_messages": "<b>❌ Не вдалося отримати текстові повідомлення для аналізу.</b>",
        "fallback": "⚠️ <b>Ліміт Gemini вичерпано. Перемикаюсь на Groq...</b>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                None,
                lambda: "API ключ для Gemini (отримати на aistudio.google.com)",
                validator=loader.validators.Hidden(),
            ),
            # Користувач вказав актуальну модель як gemini-3-flash-preview
            loader.ConfigValue(
                "model",
                "gemini-3-flash-preview", 
                lambda: "Модель Gemini"
            ),
            loader.ConfigValue(
                "groq_key",
                None,
                lambda: "API ключ для Groq (fallback)",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "groq_model",
                "llama-3.3-70b-versatile",
                lambda: "Модель Groq"
            )
        )

    def _format_markdown_to_html(self, text: str) -> str:
        """Перетворює базовий Markdown від AI у HTML для Telegram"""
        # Заміна жирного тексту **текст** на <b>текст</b>
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
        # Заміна курсиву *текст* на <i>текст</i>
        text = re.sub(r"(?<!\*)\*(?!\*)(.*?)\*", r"<i>\1</i>", text)
        # Заміна моноширинного тексту `текст` на <code>текст</code>
        text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)
        return text

    async def sumcmd(self, message):
        """[кількість] [запит] - Аналіз контексту (з підтримкою жирного шрифту)"""
        args = utils.get_args_raw(message)
        api_key = self.config["api_key"]

        if not api_key:
            await utils.answer(message, self.strings["no_api_key"])
            return

        # Парсинг аргументів
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
        try:
            async for msg in message.client.iter_messages(message.chat_id, limit=limit):
                if msg.raw_text and not msg.action:
                    sender = "Анонім"
                    if msg.sender:
                        if hasattr(msg.sender, 'first_name') and msg.sender.first_name:
                            sender = msg.sender.first_name
                        elif hasattr(msg.sender, 'title') and msg.sender.title:
                            sender = msg.sender.title
                    
                    date = msg.date.strftime("%Y-%m-%d %H:%M")
                    messages_history.append(f"{sender} [{date}]: {msg.raw_text}")
        except Exception as e:
            await utils.answer(message, f"<b>❌ Помилка при читанні історії:</b> <code>{str(e)}</code>")
            return

        if not messages_history:
            await utils.answer(message, self.strings["no_messages"])
            return

        # Реверсуємо для хронологічного порядку
        messages_history.reverse()
        context_text = "\n".join(messages_history)

        # Формування промпта з вимогою використовувати HTML
        system_instruction = (
            "Ти професійний асистент. Тобі надано історію переписки.\n"
            "ВАЖЛИВО: Використовуй HTML теги для форматування (<b>жирний</b>, <i>курсив</i>).\n"
            "Не використовуй зірочки (**) для виділення жирним, використовуй <b>."
        )

        if query:
            prompt = (
                f"{system_instruction}\n"
                f"Твоє завдання: на основі цієї переписки дай відповідь на питання: '{query}'.\n"
                f"Відповідай українською мовою.\n\n"
                f"ІСТОРІЯ ПЕРЕПИСКИ:\n{context_text}"
            )
        else:
            prompt = (
                f"{system_instruction}\n"
                f"Зроби детальний підсумок (Summary) цієї переписки ({len(messages_history)} повідомлень) українською мовою.\n"
                f"Виділи ключові теми, активних учасників та висновки.\n\n"
                f"ІСТОРІЯ ПЕРЕПИСКИ:\n{context_text}"
            )

        # Запит до API Gemini
        await self._query_gemini(message, prompt, context_text, len(messages_history))

    async def _query_gemini(self, message, prompt, context_text, msgs_count):
        api_key = self.config["api_key"]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config['model']}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    result = await resp.json()
                    
                    if resp.status == 429 or (resp.status != 200 and "quota" in str(result).lower()):
                        if self.config["groq_key"]:
                            await utils.answer(message, self.strings["fallback"])
                            return await self._query_groq(message, prompt, msgs_count)

                    if resp.status != 200:
                        error_msg = result.get("error", {}).get("message", "Unknown error")
                        await utils.answer(message, self.strings["api_error"].format(error_msg))
                        return

                    if 'candidates' not in result or not result['candidates']:
                        await utils.answer(message, "<b>❌ AI не зміг згенерувати відповідь.</b>")
                        return

                    ai_response = result['candidates'][0]['content']['parts'][0]['text']
                    await self._send_response(message, ai_response, msgs_count)

        except Exception as e:
            if self.config["groq_key"]:
                await utils.answer(message, self.strings["fallback"])
                return await self._query_groq(message, prompt, msgs_count)
            await utils.answer(message, self.strings["api_error"].format(str(e)))

    async def _query_groq(self, message, prompt, msgs_count):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config['groq_key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config["groq_model"],
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    result = await resp.json()
                    if resp.status != 200:
                        error_msg = result.get("error", {}).get("message", "Unknown Groq error")
                        await utils.answer(message, self.strings["api_error"].format(f"Groq: {error_msg}"))
                        return

                    ai_response = result['choices'][0]['message']['content']
                    await self._send_response(message, ai_response, msgs_count)
        except Exception as e:
            await utils.answer(message, self.strings["api_error"].format(f"Groq exception: {str(e)}"))

    async def _send_response(self, message, ai_response, msgs_count):
        # Виправляємо форматування (замінюємо зірочки на HTML теги, якщо AI все ж їх використав)
        formatted_response = self._format_markdown_to_html(ai_response)
        
        header = f"<b>📊 Результат аналізу ({msgs_count} повідомлень):</b>\n\n"
        full_res = header + formatted_response
        
        # Відправка результату з урахуванням лімітів Telegram
        if len(full_res) > 4096:
            for i in range(0, len(full_res), 4000):
                await utils.answer(message, full_res[i:i+4000])
        else:
            await utils.answer(message, full_res)