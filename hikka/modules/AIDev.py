from .. import loader, utils
import aiohttp
import json
import os
import re
import subprocess
import logging

logger = logging.getLogger(__name__)

@loader.tds
class AIDevMod(loader.Module):
    """🤖 AI Module Developer (Gemini AI)
Creates new modules for you via .gen command"""
    
    strings = {
        "name": "AIDev",
        "generating": "🛰 <b>Генерую модуль за запитом:</b> <code>{}</code>...",
        "error": "❌ <b>Помилка:</b> <code>{}</code>",
        "success": "✅ <b>Модуль</b> <code>{}</code> <b>створено!</b>\n🚢 <b>Git status:</b> {}",
        "no_code": "❌ <b>ШІ не повернув код. Спробуйте ще раз.</b>",
        "fixing": "🛠 <b>Виправляю модуль...</b>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                "",
                lambda: "Google Gemini API Key (Get it at aistudio.google.com)",
            ),
            loader.ConfigValue(
                "last_mod_path",
                "",
                lambda: "Path to the last generated module",
            ),
        )

    async def gencmd(self, message):
        """<query> - Create a new module using AI"""
        if not self.config["api_key"]:
            await utils.answer(
                message,
                "⚠️ <b>API Key not found!</b>\n"
                "Set it using this command:\n"
                "<code>.setcfg AIDev api_key ВАШ_КЛЮЧ</code>\n\n"
                "<i>(Отримати ключ можна на <a href='https://aistudio.google.com/app/apikey'>Google AI Studio</a>)</i>"
            )
            return

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ <b>Напишіть, що має робити модуль!</b>")
            return

        api_key = self.config["api_key"]
        await utils.answer(message, self.strings("generating").format(args))

        prompt = f"""
        Ти - професійний розробник модулів для AuthorBot (Hikka Userbot).
        Твоє завдання: написати Python-модуль за запитом користувача.
        
        ЗАПИТ КОРИСТУВАЧА: {args}
        
        СУВОРІ ПРАВИЛА:
        1. Використовуй тільки 'from .. import loader, utils' для бази.
        2. Клас МАЄ наслідуватись від 'loader.Module'.
        3. Використовуй '@loader.tds' для класу.
        4. Поверни ТІЛЬКИ чистий Python код у блоці ```python ... ```.
        5. Назва класу має бути схожою на [Name]Mod.
        6. Команди мають закінчуватися на 'cmd' (наприклад, 'testcmd').
        7. Обов'язково додавай докстрінги (описи) до класу та команд.
        8. Для відповіді на повідомлення використовуй 'await utils.answer(message, "текст")'.
        """

        code, filename = await self._query_gemini(prompt)
        
        if not code:
            await utils.answer(message, self.strings("no_code"))
            return

        # Зберігаємо файл
        mod_path = os.path.join("hikka", "modules", filename)
        try:
            with open(mod_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            self.config["last_mod_path"] = mod_path
            
            # Git push (автоматично закидаємо в репозиторій)
            git_status = await self._git_push(mod_path, f"AI-gen: {filename} for '{args[:20]}...'")
            
            await utils.answer(message, self.strings("success").format(filename, git_status))
            
            # Намагаємось завантажити модуль без перезавантаження (якщо loader це підтримує)
            try:
                await self.allmodules.commands["dlmod"](await message.respond(f".dlmod {mod_path}"))
            except:
                pass

        except Exception as e:
            await utils.answer(message, self.strings("error").format(str(e)))

    async def _query_gemini(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.config['api_key']}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                try:
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    code_match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
                    if not code_match:
                        code_match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
                    
                    code = code_match.group(1) if code_match else text
                    
                    # Витягуємо назву файлу з назви класу
                    fn_match = re.search(r"class (\w+)Mod", code)
                    filename = f"{fn_match.group(1)}.py" if fn_match else "GeneratedMod.py"
                    
                    return code, filename
                except Exception as e:
                    logger.error(f"Gemini error: {e}")
                    return None, None

    async def _git_push(self, file_path, commit_msg):
        try:
            # Виконуємо git команди прямо на сервері
            subprocess.run(["git", "add", file_path], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
            subprocess.run(["git", "push"], check=True, capture_output=True)
            return "🚀 Запушено в GitHub!"
        except Exception as e:
            return f"⚠️ Збережено локально, але Git видав помилку: {str(e)}"
