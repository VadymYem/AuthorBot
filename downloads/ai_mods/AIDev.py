#meta developer: chernykh-mykhailo (@myshcode_ai)
# t.me/myshcode_ai

from .. import loader, utils
import aiohttp
import asyncio
import json
import os
import re
import logging
import html

logger = logging.getLogger(__name__)

@loader.tds
class AIDevMod(loader.Module):
    """🤖 AI Module Developer (Gemini AI)
    Creates new modules for you via .gen command

    👤 Developer: chernykh-mykhailo (@Div4unka_z_kare)
    🌐 Channel: t.me/myshcode_ai"""
    
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
            "api_key", "", "Google Gemini API Key",
            "model", "gemini-3-flash-preview", "Gemini Model Name (e.g. gemini-3-flash-preview)",
            "last_mod_path", "", "Path to the last generated module"
        )

    @loader.command()
    async def gencmd(self, message):
        """<query> - Create a new module using AI"""
        if not self.config["api_key"]:
            await utils.answer(
                message,
                "⚠️ <b>API Key not found!</b>\n"
                "Спробуйте встановити його так:\n"
                "<code>.setkey ВАШ_КЛЮЧ</code>"
            )
            return

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ <b>Напишіть, що має робити модуль!</b>\nПриклад: <code>.gen напиши модуль для показу курсу валют</code>")
            return

        await utils.answer(message, self.strings("generating").format(args))

        # Check if we are modifying an existing module
        context = ""
        # Try to find a filename in the query (e.g. "update Currency.py")
        fn_match = re.search(r"([\w.-]+)\.py", args)
        target_fn = fn_match.group(0) if fn_match else None

        # Search everywhere we might store modules
        this_path = getattr(self, "__origin__", None)
        search_dirs = [
            os.path.join("downloads", "ai_mods"),
            os.path.join("hikka", "modules"),
            os.path.join("downloads"),
            os.getcwd()
        ]
        target_path = None
        if this_path:
            search_dirs.append(os.path.dirname(os.path.abspath(this_path)))
            
            if target_fn:
                for d in search_dirs:
                    if d and os.path.exists(os.path.join(d, target_fn)):
                        target_path = os.path.join(d, target_fn)
                        break
            
            if target_path and os.path.exists(target_path):
                with open(target_path, "r", encoding="utf-8") as f:
                    old_code = f.read()
                context = f"\nПОТОЧНИЙ КОД МОДУЛЯ {target_fn}:\n```python\n{old_code}\n```\nЯКЩО КОРИСТУВАЧ ПРОСИТЬ ЗМІНИТИ, ОНОВИ ЦЕЙ КОД. ЯКЩО НІ - ПИШИ З НУЛЯ.\n"

        prompt = f"""
        Ти - професійний розробник модулів для AuthorBot (Hikka Userbot).
        Твоє завдання: написати Python-модуль за запитом користувача.
        {context}
        ЗАПИТ КОРИСТУВАЧА: {args}
        
        СУВОРІ ПРАВИЛА:
        1. ЗАВЖДИ починай код з мета-данних (БЕЗ виключень):
           #meta developer: chernykh-mykhailo (@Div4unka_z_kare)
           # t.me/myshcode_ai
        2. Використовуй тільки 'from .. import loader, utils' для бази.
        3. Клас МАЄ наслідуватись від 'loader.Module'.
        4. Використовуй '@loader.tds' для класу.
        5. Поверни ТІЛЬКИ чистий Python код у блоці ```python ... ```.
        6. Назва класу має быть схожою на [Name]Mod.
        7. Команди мають закінчуватися на 'cmd' (наприклад, 'testcmd').
        8. Обов'язково додавай докстрінги (описи) до класу та команд.
        9. Для відповіді на повідомлення використовуй 'await utils.answer(message, "текст")'.
        10. ТІЛЬКИ ЯКЩО модуль передбачає роботу з ШІ: додай 'api_key' та 'model' (дефолт: {self.config['model']}) у loader.ModuleConfig. Якщо ШІ не потрібен - НЕ додавай ці параметри та ніякі команди перевірки Gemini.
        11. ОБЕРЕЖНО З ФЛУДОМ: Якщо в коді є великі цикли або надсилання багатьох повідомлень, ОБОВ'ЯЗКОВО використовуй 'await asyncio.sleep(1.0)' між викликами. Не роби більше 5-10 викликів API поспіль без затримки. Бот не має виглядати як спамер.
        12. БЕЗПЕКА: Завжди ігноруй або обробляй ситуації, коли повідомлення може бути порожнім (msg.raw_text or "").
        """

        code, filename = await self._query_gemini(message, prompt)
        
        if not code:
            return # Помилка вже виведена в _query_gemini

        # Find Git root to ensure we save INSIDE the repo
        code_ret, git_root, _ = await self._run_git("rev-parse", "--show-toplevel")
        if code_ret != 0:
            git_root = os.getcwd()

        ai_mods_dir = os.path.join(git_root, "downloads", "ai_mods")
        if not os.path.exists(ai_mods_dir):
            os.makedirs(ai_mods_dir, exist_ok=True)
            
        mod_path = os.path.join(ai_mods_dir, filename)
        try:
            with open(mod_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            self.config["last_mod_path"] = mod_path
            git_status = await self._git_push(mod_path, f"AI-gen: {filename} for '{args[:20]}...'")
            
            # Check if git push failed - send file as fallback
            git_failed = "⚠️" in git_status or "error" in git_status.lower() or "таймаут" in git_status.lower()
            
            if git_failed:
                # Send file to chat as fallback
                try:
                    await self._client.send_file(
                        message.peer_id,
                        mod_path,
                        caption=(
                            f"📦 <b>Модуль</b> <code>{filename}</code> <b>згенеровано!</b>\n"
                            f"⚠️ <b>Git push не вдався:</b> {git_status}\n\n"
                            f"📥 <b>Встановіть вручну:</b>\n"
                            f"<code>.lm</code> (reply на файл)"
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to send file: {e}")
            else:
                await utils.answer(message, self.strings("success").format(filename, git_status))
            
            # Direct loading attempt (always try to load locally)
            try:
                await self.aimcmd(message, mod_path)
                
                # Auto-configure the new module
                module_name = filename.replace(".py", "")
                await asyncio.sleep(1) # Give it a second to register
                new_mod = self.allmodules.lookup(module_name)
                if new_mod and hasattr(new_mod, "config"):
                    changed = False
                    if "api_key" in new_mod.config and not new_mod.config["api_key"]:
                        new_mod.config["api_key"] = self.config["api_key"]
                        changed = True
                    if "model" in new_mod.config:
                        new_mod.config["model"] = self.config["model"]
                        changed = True
                    
                    if changed:
                        config_msg = "⚙️ <b>Конфігурація (API Key/Model) застосована автоматично!</b>"
                        if git_failed:
                            await message.respond(config_msg)
                        else:
                            await utils.answer(message, self.strings("success").format(filename, f"{git_status}\n{config_msg}"))
            except Exception as e:
                logger.error(f"Instant load/config failed: {e}")

        except Exception as e:
            await utils.answer(message, self.strings("error").format(str(e)))

    @loader.command()
    async def setkeycmd(self, message):
        """<key> - Set Gemini API Key directly"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ <b>Введіть ключ!</b>")
            return
        
        self.config["api_key"] = args
        await utils.answer(message, "✅ <b>API Ключ збережено!</b>\nТепер спробуйте <code>.gen ...</code>")

    @loader.command()
    async def setmodelcmd(self, message):
        """<model> - Set Gemini model name"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, f"📌 <b>Поточна модель:</b> <code>{self.config['model']}</code>\nВикористовуйте: <code>.setmodel НазваМоделі</code>")
            return
        
        self.config["model"] = args
        await utils.answer(message, f"✅ <b>Модель змінена на:</b> <code>{args}</code>")

    @loader.command()
    async def lmodscmd(self, message):
        """- List all files in modules folders"""
        try:
            # Safe way to get current file path in Hikka
            this_path = getattr(self, "__origin__", None)
            if not this_path:
                try:
                    this_path = os.path.abspath(__file__)
                except NameError:
                    this_path = "Unknown"

            dirs_to_check = [
                os.path.join("hikka", "modules"),
                os.path.join("downloads", "ai_mods"),
                os.path.join("downloads"),
                os.getcwd()
            ]
            
            if this_path != "Unknown":
                dirs_to_check.append(os.path.dirname(this_path))
            
            all_files = set()
            for d in dirs_to_check:
                if os.path.exists(d):
                    for f in os.listdir(d):
                        if f.endswith(".py"):
                            all_files.add(f)
            
            if not all_files:
                await utils.answer(message, "📂 <b>Файлів модулів не знайдено.</b>")
                return

            this_file = os.path.basename(this_path) if this_path != "Unknown" else "AIDev.py"
            msg = f"📍 <b>Поточний AIDev:</b> <code>{this_path}</code>\n"
            msg += "📂 <b>Знайдені модулі:</b>\n\n"
            
            # Sort and mark
            for f in sorted(list(all_files)):
                star = "⭐ " if f == this_file else "• "
                info = ""
                
                # Try to find developer info
                found_path = None
                for d in dirs_to_check:
                    p = os.path.join(d, f)
                    if os.path.exists(p):
                        found_path = p
                        break
                
                if found_path:
                    try:
                        with open(found_path, "r", encoding="utf-8") as file:
                            header = file.read(500)
                            dev_match = re.search(r"# ?meta developer: ?(.+)", header)
                            if dev_match:
                                info = f" [by {dev_match.group(1).strip()}]"
                    except:
                        pass

                if os.path.exists(os.path.join("downloads", "ai_mods", f)):
                    msg += f"🤖 <code>{f}</code> (AI){info}\n"
                elif os.path.exists(os.path.join("hikka", "modules", f)):
                    msg += f"⚙️ <code>{f}</code> (Sys){info}\n"
                else:
                    msg += f"{star}<code>{f}</code>{info}\n"
            
            msg += f"\n💡 Використовуйте <code>.vmod назва</code> щоб переглянути код."
            await utils.answer(message, msg)
        except Exception as e:
            await utils.answer(message, f"❌ <b>Помилка:</b> <code>{str(e)}</code>")

    @loader.command()
    async def vmodcmd(self, message):
        """<name> - View module source code"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ <b>Вкажіть назву модуля!</b>")
            return
        
        filename = args if args.endswith(".py") else f"{args}.py"
        paths = [
            os.path.join("downloads", "ai_mods", filename),
            os.path.join("hikka", "modules", filename),
            os.path.join("downloads", filename),
            filename
        ]
        
        path = next((p for p in paths if os.path.exists(p)), None)
        
        if not path:
            await utils.answer(message, f"❌ <b>Файл</b> <code>{filename}</code> <b>не знайдено.</b>")
            return
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            
            # If code is too long, send as file
            if len(code) > 3000:
                with open(filename, "w", encoding="utf-8") as tmp:
                    tmp.write(code)
                await self._client.send_file(message.peer_id, filename, caption=f"📄 <b>Код модуля:</b> <code>{filename}</code>")
                os.remove(filename)
            else:
                await utils.answer(message, f"📄 <b>Код модуля</b> <code>{filename}</code>:\n\n```python\n{code}\n```")
        except Exception as e:
            await utils.answer(message, f"❌ <b>Помилка:</b> <code>{str(e)}</code>")

    @loader.command()
    async def vtxtcmd(self, message):
        """<name> - View module source code as text blocks"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ <b>Вкажіть назву модуля!</b>")
            return
        
        filename = args if args.endswith(".py") else f"{args}.py"
        paths = [
            os.path.join("downloads", "ai_mods", filename),
            os.path.join("hikka", "modules", filename),
            os.path.join("downloads", filename),
            filename
        ]
        
        path = next((p for p in paths if os.path.exists(p)), None)
        
        if not path:
            await utils.answer(message, f"❌ <b>Файл</b> <code>{filename}</code> <b>не знайдено.</b>")
            return
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            
            await utils.answer(message, f"📄 <b>Текст модуля</b> <code>{filename}</code>:")
            
            # Split code into chunks of ~3500 chars 
            chunks = [code[i:i+3500] for i in range(0, len(code), 3500)]
            
            if len(chunks) > 15:
                await utils.answer(message, "⚠️ <b>Файл занадто великий!</b> Надішлю перші 15 частин, решту дивіться через <code>.vmod</code> (файлом).")
                chunks = chunks[:15]

            for i, chunk in enumerate(chunks):
                # Properly escape HTML entities to prevent breaking the tags
                safe_chunk = html.escape(chunk)
                await message.respond(f"📦 <b>Частина {i+1}/{len(chunks)}:</b>\n\n<pre><code>{safe_chunk}</code></pre>")
                await asyncio.sleep(1.2) # Safer delay for userbots
                
        except Exception as e:
            await utils.answer(message, f"❌ <b>Помилка:</b> <code>{str(e)}</code>")

    @loader.command()
    async def gmovecmd(self, message):
        """<name> - Move module from hikka/modules to downloads/ai_mods"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ <b>Вкажіть назву модуля!</b>")
            return
        
        code_ret, git_root, _ = await self._run_git("rev-parse", "--show-toplevel")
        if code_ret != 0:
            git_root = os.getcwd()
        
        filename = args if args.endswith(".py") else f"{args}.py"
        old_path = os.path.join(git_root, "hikka", "modules", filename)
        new_dir = os.path.join(git_root, "downloads", "ai_mods")
        new_path = os.path.join(new_dir, filename)
        
        if os.path.exists(new_path):
            await utils.answer(message, f"ℹ️ <b>Модуль</b> <code>{filename}</code> <b>вже знаходиться в ai_mods.</b>")
            return
            
        if not os.path.exists(old_path):
            await utils.answer(message, f"❌ <b>Модуль</b> <code>{filename}</code> <b>не знайдено в hikka/modules.</b>")
            return
            
        try:
            os.makedirs(new_dir, exist_ok=True)
            os.rename(old_path, new_path)
            
            # Push changes to Git
            git_status = await self._git_push(new_path, f"Move {filename} to ai_mods")
            
            await utils.answer(
                message, 
                f"🚚 <b>Модуль</b> <code>{filename}</code> <b>успішно перенесено в ai_mods!</b>\n"
                f"🔄 <b>Git:</b> {git_status}\n"
                f"Перезавантажте його через <code>.aim {filename}</code>"
            )
        except Exception as e:
            await utils.answer(message, f"❌ <b>Помилка перенесення:</b> <code>{str(e)}</code>")

    @loader.command()
    async def gdelcmd(self, message):
        """<name> - Delete module file"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ <b>Вкажіть назву модуля для видалення!</b>")
            return
            
        filename = args if args.endswith(".py") else f"{args}.py"
        # Search for the file to delete
        paths = [
            os.path.join("downloads", "ai_mods", filename),
            os.path.join("hikka", "modules", filename),
            os.path.join("downloads", filename),
            filename
        ]
        
        path_to_del = next((p for p in paths if os.path.exists(p)), None)
        
        if not path_to_del:
            await utils.answer(message, f"❌ <b>Файл</b> <code>{filename}</code> <b>не знайдено.</b>")
            return
            
        try:
            # Find git root before deleting if possible
            git_root = self._find_git_root(os.path.dirname(os.path.abspath(path_to_del)))
            os.remove(path_to_del)
            
            # Push changes to Git
            git_status = "Skipped"
            if git_root:
                await self._run_git("add", "-A", cwd=git_root)
                push = await self._git_push(git_root, f"Delete module {filename}")
                git_status = push
                
            await utils.answer(
                message, 
                f"🗑 <b>Файл</b> <code>{filename}</code> <b>видалено!</b>\n"
                f"🔄 <b>Git:</b> {git_status}\n"
                f"Не забудьте зробити <code>.unload {args.replace('.py', '')}</code>"
            )
        except Exception as e:
            await utils.answer(message, f"❌ <b>Помилка видалення:</b> <code>{str(e)}</code>")

    @loader.command()
    async def aimcmd(self, message, path=None):
        """[path] - Force install module from local path"""
        target = path or utils.get_args_raw(message)
        if not target:
            await utils.answer(message, "❌ <b>Вкажіть назву модуля!</b>")
            return

        # Prepare potential paths
        filename = target if target.endswith(".py") else f"{target}.py"
        paths_to_check = [
            os.path.join("downloads", "ai_mods", filename), # Our new AI dir
            os.path.join("hikka", "modules", filename),     # Standard hikka modules
            os.path.join("downloads", filename),             # Downloads dir
            filename,                                       # Current dir
            os.path.abspath(filename)                       # Absolute current
        ]

        found_path = None
        for p in paths_to_check:
            if os.path.exists(p) and os.path.isfile(p):
                found_path = p
                break

        if not found_path:
            await utils.answer(message, f"❌ <b>Файл не знайдено:</b> <code>{filename}</code>\nЯ шукав у: <code>hikka/modules/</code>")
            return

        await utils.answer(message, f"📥 <b>Завантажую:</b> <code>{found_path}</code>...")
        
        try:
            # We first try to find the 'Loader' module to use its advanced loading logic
            loader = self.allmodules.lookup("Loader")
            if loader and hasattr(loader, "load_module"):
                with open(found_path, "r", encoding="utf-8") as f:
                    code = f.read()
                # load_module(code, message, name, origin, save_fs=True)
                await loader.load_module(code, message, name=filename, origin="<file>", save_fs=True)
                await utils.answer(message, f"✅ <b>Модуль завантажено через Loader!</b>")
            else:
                # Fallback to direct registration if Loader is not available
                await self.allmodules._register_modules([os.path.abspath(found_path)], origin="<file>")
                await utils.answer(message, f"✅ <b>Модуль зареєстровано trực tiếp!</b>")
        except Exception as e:
            # Final fallback: try standard .dlmod command
            try:
                await self.allmodules.commands["dlmod"](await message.respond(f".dlmod {os.path.abspath(found_path)}"))
            except Exception as e2:
                await utils.answer(message, f"❌ <b>Помилка:</b> <code>{str(e)}</code>\n(також: {str(e2)})")

    @loader.command()
    async def gpushcmd(self, message):
        """[message] - Commit and push all changes to Git"""
        args = utils.get_args_raw(message) or "Update modules via AI"
        await utils.answer(message, "🔌 <b>Git: Додаю файли та пушу...</b>")
        
        try:
            code_ret, git_root, _ = await self._run_git("rev-parse", "--show-toplevel")
            if code_ret != 0:
                git_root = os.getcwd()

            # Force add AI mods since Downloads is ignored
            await self._run_git("add", "-f", "downloads/ai_mods/", cwd=git_root)
            await self._run_git("add", "hikka/modules/", cwd=git_root)
            
            await self._run_git("commit", "-m", args, cwd=git_root)
            code_ret, stdout, stderr = await self._run_git("push", cwd=git_root, timeout=30)
            
            if code_ret == 0:
                await utils.answer(message, "🚀 <b>Усі зміни успішно відправлені в GitHub!</b>")
            else:
                await utils.answer(message, f"❌ <b>Помилка пушу:</b>\n<code>{stderr}</code>")
        except Exception as e:
            await utils.answer(message, f"❌ <b>Помилка Git:</b>\n<code>{str(e)}</code>")

    @loader.command()
    async def gpullcmd(self, message):
        """- Pull latest changes from Git"""
        await utils.answer(message, "🔌 <b>Git: Завантажую оновлення (Pull)...</b>")
        
        try:
            code_ret, git_root, _ = await self._run_git("rev-parse", "--show-toplevel")
            if code_ret != 0:
                git_root = os.getcwd()

            code_ret, stdout, stderr = await self._run_git("pull", cwd=git_root, timeout=30)
            
            if code_ret == 0:
                await utils.answer(message, f"📥 <b>Оновлення отримано!</b>\n<pre>{stdout}</pre>")
            else:
                if "CONFLICT" in stderr or "CONFLICT" in stdout or "resolve your current index" in stderr:
                    await self.inline.form(
                        message=message,
                        text=(
                            "⚠️ <b>Конфлікт при оновленні!</b>\n"
                            "Ви змінили файли і на сервері, і в GitHub.\n"
                            "<b>Оберіть дію:</b>"
                        ),
                        reply_markup=[
                            [{"text": "📥 Взяти з GitHub (Remote)", "callback": self._git_resolve, "args": ("remote", git_root)}],
                            [{"text": "💾 Залишити мої (Abort)", "callback": self._git_resolve, "args": ("abort", git_root)}],
                            [{"text": "🔀 Злити (Stash & Pull)", "callback": self._git_resolve, "args": ("stash", git_root)}],
                            [{"text": "❌ Закрити", "action": "close"}]
                        ]
                    )
                else:
                    await utils.answer(message, f"❌ <b>Помилка Pull:</b>\n<code>{stderr or stdout}</code>")
        except Exception as e:
            await utils.answer(message, f"❌ <b>Помилка Git:</b>\n<code>{str(e)}</code>")

    async def _git_resolve(self, call, action, git_root):
        """Callback for git conflict resolution"""
        await call.edit("⏳ <b>Виконую...</b>")
        try:
            if action == "remote":
                await self._run_git("fetch", "--all", cwd=git_root)
                await self._run_git("reset", "--hard", "origin/main", cwd=git_root)
                text = "✅ <b>Файли скинуто до стану GitHub! (Локальні зміни видалено)</b>"
            elif action == "abort":
                await self._run_git("merge", "--abort", cwd=git_root)
                text = "✅ <b>Злиття скасовано. Ваші локальні файли не змінено.</b>"
            elif action == "stash":
                await self._run_git("stash", cwd=git_root)
                await self._run_git("pull", cwd=git_root, timeout=30)
                await self._run_git("stash", "pop", cwd=git_root)
                text = "✅ <b>Спробував злити через Stash. Перевірте файли!</b>"
            
            await call.edit(text, reply_markup=[{"text": "❌ Закрити", "action": "close"}])
        except Exception as e:
            await call.edit(f"❌ <b>Помилка:</b> <code>{str(e)}</code>")

    async def _query_gemini(self, message, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config['model']}:generateContent?key={self.config['api_key']}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        logger.info("AIDev: Starting Gemini API request...")
        timeout = aiohttp.ClientTimeout(total=90)  # 90 sec max
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as resp:
                    logger.info(f"AIDev: Gemini responded with status {resp.status}")
                    data = await resp.json()
                    
                    if "candidates" not in data:
                        error_msg = data.get("error", {}).get("message", "Unknown API Error")
                        await utils.answer(message, self.strings("error").format(f"Gemini API: {error_msg}"))
                        logger.error(f"Gemini error response: {data}")
                        return None, None
                        
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    code_match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
                    if not code_match:
                        code_match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
                    
                    code = code_match.group(1) if code_match else text
                    fn_match = re.search(r"class (\w+)Mod", code)
                    filename = f"{fn_match.group(1)}.py" if fn_match else "GeneratedMod.py"
                    logger.info(f"AIDev: Code parsed successfully, filename: {filename}")
                    return code, filename
                    
        except asyncio.TimeoutError:
            logger.error("AIDev: Gemini API request timed out after 90s")
            await utils.answer(message, self.strings("error").format("⏱️ Таймаут: Gemini не відповів за 90 секунд"))
            return None, None
        except aiohttp.ClientError as e:
            logger.error(f"AIDev: Network error: {e}")
            await utils.answer(message, self.strings("error").format(f"Мережева помилка: {str(e)}"))
            return None, None
        except Exception as e:
            logger.error(f"AIDev: Gemini parsing error: {e}")
            await utils.answer(message, self.strings("error").format(f"Parsing: {str(e)}"))
            return None, None

    async def _run_git(self, *args, cwd=None, timeout=15):
        """Run git command asynchronously with timeout"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return proc.returncode, stdout.decode().strip(), stderr.decode().strip()
        except asyncio.TimeoutError:
            logger.warning(f"AIDev: Git command timed out: git {' '.join(args)}")
            try:
                proc.kill()
            except:
                pass
            return -1, "", "Таймаут команди Git"
        except Exception as e:
            logger.error(f"AIDev: Git subprocess error: {e}")
            return -1, "", str(e)

    async def _git_push(self, file_path, commit_msg):
        try:
            # Find the git root directory
            code, stdout, stderr = await self._run_git("rev-parse", "--show-toplevel")
            git_root = stdout if code == 0 else os.getcwd()

            # Ensure path is absolute for git commands
            abs_file_path = os.path.abspath(file_path)

            # Stage changes (use -f to force add even if ignored by .gitignore)
            await self._run_git("add", "-f", abs_file_path, cwd=git_root)
            
            # Commit changes
            await self._run_git("commit", "-m", commit_msg, cwd=git_root)
            
            # Push to origin
            code, stdout, stderr = await self._run_git("push", cwd=git_root, timeout=30)
            if code != 0:
                return f"⚠️ Git push error: {stderr}"

            return "🚀 Запушено в GitHub!"
        except Exception as e:
            logger.error(f"AIDev: Git push error: {e}")
            return f"⚠️ Внутрішня помилка Git: {str(e)}"