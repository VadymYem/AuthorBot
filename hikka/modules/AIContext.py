import google.generativeai as genai
from .. import loader, utils
import datetime

@loader.tds
class AIContextMod(loader.Module):
    """Модуль для аналізу контексту чату за допомогою Gemini AI"""

    strings = {
        "name": "AIContext",
        "no_api_key": "<b>🚫 Не вказано Gemini API Key!</b>\nОтримай його на <a href='https://aistudio.google.com/app/apikey'>Google AI Studio</a> та пропиши в конфігах: <code>.config AIContext</code>",
        "processing": "<b>🤖 Аналізую повідомлення...</b>",
        "no_context": "<b>❌ Не вдалося зібрати історію повідомлень.</b>",
        "error": "<b>❌ Помилка AI:</b> <code>{}</code>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                None,
                lambda: "API ключ для Google Gemini",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "model_name",
                "gemini-1.5-flash",  # Використовуємо стабільну, оскільки gemini-3 не існує, 
                                     # але логіка дозволяє вписати будь-яку за запитом користувача
                lambda: "Назва моделі Gemini",
            ),
        )

    async def sumcmd(self, message):
        """[кількість] [запит] - Аналізує історію повідомлень та робить Summary або шукає відповідь"""
        args = utils.get_args(message)
        count = 50
        query = ""

        if not self.config["api_key"]:
            await utils.answer(message, self.strings["no_api_key"])
            return

        if args:
            if args[0].isdigit():
                count = int(args[0])
                query = " ".join(args[1:])
            else:
                query = " ".join(args)

        await utils.answer(message, self.strings["processing"])

        # Збір історії повідомлень
        history = []
        async for msg in message.client.iter_messages(message.peer_id, limit=count):
            if msg.id == message.id:
                continue
            
            sender = "Анонім"
            if msg.sender:
                sender = getattr(msg.sender, 'first_name', '') or getattr(msg.sender, 'title', 'Анонім')
            
            date = msg.date.strftime("%Y-%m-%d %H:%M")
            text = msg.text or (msg.caption if msg.caption else "[Медіа-повідомлення]")
            
            if text:
                history.append(f"{sender} [{date}]: {text}")

        if not history:
            await utils.answer(message, self.strings["no_context"])
            return

        history.reverse()  # Порядок від старого до нового
        context_text = "\n".join(history)

        # Формування промпта
        if query:
            prompt = (
                f"Ти — професійний аналітик чатів. Твоє завдання: базуючись ТІЛЬКИ на наданому контексті переписки, "
                f"відповісти на запитання: \"{query}\". Якщо відповіді немає в тексті, так і скажи. "
                f"Відповідай лаконічно українською мовою.\n\nКОНТЕКСТ:\n{context_text}"
            )
        else:
            prompt = (
                f"Ти — асистент, що робить Summary переписки. На основі наданих повідомлень зроби короткий "
                f"та влучний огляд того, про що спілкувалися користувачі. "
                f"Відповідай українською мовою.\n\nПОВІДОМЛЕННЯ:\n{context_text}"
            )

        try:
            genai.configure(api_key=self.config["api_key"])
            # Використовуємо назву моделі з запиту користувача, якщо вона вказана в конфігу, 
            # інакше gemini-1.5-flash (найшвидша зараз)
            model = genai.GenerativeModel(self.config["model_name"] or "gemini-1.5-flash")
            
            response = await model.generate_content_async(prompt)
            
            final_text = f"<b>✨ Результат аналізу ({count} пов.):</b>\n\n{response.text}"
            await utils.answer(message, final_text)

        except Exception as e:
            await utils.answer(message, self.strings["error"].format(str(e)))