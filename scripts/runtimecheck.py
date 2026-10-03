#!/usr/bin/env python3
"""Offline regression checks for startup, module loading, artwork and persistence."""

from __future__ import annotations

import asyncio
import base64
import importlib
import inspect
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def import_all_modules():
    from acbot import loader

    count = 0
    for path in sorted((ROOT / "acbot").rglob("*.py")):
        if path.name == "__main__.py":
            continue
        name = ".".join(path.relative_to(ROOT).with_suffix("").parts)
        module = importlib.import_module(name)
        for cls in vars(module).values():
            if inspect.isclass(cls) and cls.__module__ == name and issubclass(cls, loader.Module):
                cls()
                count += 1
    for path in sorted((ROOT / "downloads" / "ai_mods").glob("*.py")):
        name = f"acbot.modules._audit_{path.stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for cls in vars(module).values():
            if inspect.isclass(cls) and cls.__module__ == name and issubclass(cls, loader.Module):
                cls()
                count += 1
    print(f"Imported all core files; constructed {count} core/bundled modules.")


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_info_command_and_inline_use_only_existing_buttons(self):
        from acbot.modules.info import acbotInfoMod
        mod = acbotInfoMod()
        mod.inline = SimpleNamespace(form=AsyncMock(), brand_photo=AsyncMock(return_value="AgAC" + "a" * 40))
        mod._render_info = Mock(return_value="<b>AuthorBot</b>")
        mod.strings = lambda key: key
        await mod.infocmd(Mock())
        self.assertIn("photo", mod.inline.form.call_args.kwargs)
        result = await mod.info_inline_handler(Mock())
        self.assertIn("photo", result)
        mod.config["disable_inline_banner"] = True
        result = await mod.info_inline_handler(Mock())
        self.assertIn("message", result)
        self.assertNotIn("photo", result)
        mod.config["custom_button1"] = ["Incomplete"]
        self.assertIsNone(mod._get_mark(1))

    async def test_module_download_reports_actual_load_result(self):
        from acbot.modules.loader import LoaderMod
        mod = LoaderMod()
        mod._storage = SimpleNamespace(fetch=AsyncMock(return_value="class Valid: pass"))
        mod.load_module = AsyncMock(return_value=False)
        self.assertEqual(await mod.download_and_install("https://example.org/test.py"), 0)
        mod.load_module.return_value = True
        self.assertEqual(await mod.download_and_install("https://example.org/test.py"), 1)

    async def test_failed_module_registration_returns_false(self):
        from acbot.modules.loader import LoaderMod
        mod = LoaderMod()
        mod.strings = lambda key: key
        mod.allmodules = SimpleNamespace(register_module=AsyncMock(side_effect=SyntaxError("invalid source")))
        with self.assertLogs("acbot.modules.loader", level="ERROR"):
            self.assertFalse(await mod.load_module("class Broken: pass", None))

    async def test_module_catalog_order_and_cache_count(self):
        from acbot.modules.loader import LoaderMod
        mod = LoaderMod()
        mod.config["ADDITIONAL_REPOS"] = []
        mod._get_repo = AsyncMock(return_value=["first", "gg.gg", "first", "last"])
        catalog = await mod.get_repo_list()
        self.assertEqual([url.rsplit("/", 1)[-1] for url in next(iter(catalog.values())).values()],
                         ["first.py", "gg.gg.py", "last.py"])
        mod._links_cache = {"repo": {"exp": 123, "data": ["a", "b", "c"]}}
        self.assertEqual(mod.inspect_cache(), 3)
        self.assertEqual(mod.flush_cache(), 3)

    async def test_stopping_and_restarting_background_loop(self):
        from acbot.loader import InfiniteLoop, StopLoop
        entered = asyncio.Event()
        async def work(_):
            entered.set()
            raise StopLoop()
        loop = InfiniteLoop(work, 0.01, False, False, None)
        loop.module_instance = SimpleNamespace()
        self.assertTrue(await loop.stop())
        loop.start()
        await asyncio.wait_for(entered.wait(), 1)
        await asyncio.wait_for(loop._wait_for_stop.wait(), 1)
        self.assertFalse(loop.status)
        entered.clear()
        loop.start()
        await asyncio.wait_for(entered.wait(), 1)
        await loop.stop()
        self.assertFalse(loop.status)

    async def test_cancellation_before_module_is_assigned(self):
        from acbot.loader import InfiniteLoop
        loop = InfiniteLoop(AsyncMock(), 1, False, False, None)
        loop.start()
        await asyncio.sleep(0)
        await asyncio.wait_for(loop.stop(), 1)
        self.assertTrue(loop._task.done())

    async def test_photo_result_supports_urls_and_cached_files(self):
        from acbot.branding import photo_result
        self.assertIn("photo_url", photo_result("https://example.org/a.jpg", id="1").to_python())
        cached = photo_result("AgAC" + "a" * 40, id="2").to_python()
        self.assertIn("photo_file_id", cached)
        self.assertNotIn("photo_url", cached)

    async def test_artwork_upload_is_cached_and_serialized(self):
        from acbot.inline.core import InlineManager
        db_data = {}
        manager = InlineManager.__new__(InlineManager)
        manager._brand_photo_lock = asyncio.Lock()
        manager._me = 123
        manager.bot_id = 456
        manager._db = SimpleNamespace(
            get=lambda section, key, default: db_data.get(key, default),
            set=lambda section, key, value: db_data.update({key: value}),
        )
        sent = SimpleNamespace(photo=[SimpleNamespace(file_id="cached_photo")],
                               chat=SimpleNamespace(id=123), message_id=1)
        manager.bot = SimpleNamespace(send_photo=AsyncMock(return_value=sent), delete_message=AsyncMock())
        result = await asyncio.gather(manager.brand_photo(), manager.brand_photo())
        self.assertEqual(result, ["cached_photo", "cached_photo"])
        manager.bot.send_photo.assert_awaited_once()

    async def test_public_rich_page_uploads_bundled_artwork(self):
        from acbot.modules.inline_stuff import InlineStuff, START_RICH
        mod = InlineStuff()
        mod._public_rich = lambda page: START_RICH
        mod.inline = SimpleNamespace(rich=SimpleNamespace(send=AsyncMock()))
        message = SimpleNamespace(chat=SimpleNamespace(id=123), answer=AsyncMock())
        await mod._send_public_page(message, "start")
        payload = mod.inline.rich.send.call_args.kwargs
        self.assertIn("tg://photo?id=bot_artwork", payload["html"])
        self.assertTrue(payload["files"]["bot_artwork"].is_file())
        self.assertEqual(payload["media"][0]["media"]["media"], "attach://bot_artwork")
        message.answer.assert_not_awaited()

    async def test_public_page_fallback_remains_available(self):
        from acbot.modules.inline_stuff import InlineStuff, START_RICH
        mod = InlineStuff()
        mod._public_rich = lambda page: START_RICH
        mod.inline = SimpleNamespace(rich=SimpleNamespace(send=AsyncMock(side_effect=RuntimeError("offline"))))
        message = SimpleNamespace(chat=SimpleNamespace(id=123), answer=AsyncMock())
        with self.assertLogs("acbot.modules.inline_stuff", level="WARNING"):
            await mod._send_public_page(message, "start")
        message.answer.assert_awaited_once()

    async def test_rich_transport_multipart_and_handle_cleanup(self):
        from acbot.branding import BOT_PHOTO
        from acbot.inline.rich import RichBotAPI
        captured = {}
        def post(url, **kwargs):
            captured.update(kwargs)
            self.assertTrue(kwargs["files"]["art"][1].read().startswith(b"\xff\xd8"))
            self.assertEqual(json.loads(kwargs["data"]["rich_message"])["html"], "<p>Photo</p>")
            return SimpleNamespace(ok=True, json=lambda: {"ok": True, "result": {"message_id": 7}})
        with patch("acbot.inline.rich.requests.post", side_effect=post):
            result = await RichBotAPI("123:token").send(123, html="<p>Photo</p>", files={"art": BOT_PHOTO})
        self.assertEqual(result["message_id"], 7)
        self.assertTrue(captured["files"]["art"][1].closed)

    async def test_rich_transport_validation_and_redacted_errors(self):
        from acbot.inline.rich import RichBotAPI, RichMessageError
        api = RichBotAPI("123:secret")
        with self.assertRaises(ValueError):
            await api.send(1, html="a", markdown="b")
        with self.assertRaises(ValueError):
            await api.request("../invalid")
        with patch("acbot.inline.rich.requests.post", return_value=SimpleNamespace(ok=False, json=lambda: {"ok": False, "description": "123:secret"})):
            with self.assertRaises(RichMessageError) as error:
                await api.send(1, html="a")
            self.assertNotIn("secret", str(error.exception))
        with patch("acbot.inline.rich.requests.post", return_value=SimpleNamespace(ok=True, json=lambda: [])):
            with self.assertRaises(RichMessageError):
                await api.send(1, html="a")

    async def test_nested_aiogram_payload_is_serializable(self):
        from aiogram.types import InlineKeyboardButton
        from acbot.inline.rich import RichBotAPI
        value = RichBotAPI._jsonable({"rows": [[InlineKeyboardButton("Site", url="https://authorche.top")]]})
        self.assertEqual(json.loads(json.dumps(value))["rows"][0][0]["text"], "Site")

    async def test_multilingual_translation_pack(self):
        from acbot.translations import BaseTranslator
        result = BaseTranslator()._get_pack_raw("ua:\n  example:\n    greeting: Привіт\nen:\n  example:\n    greeting: Hello\n", ".yml")
        self.assertEqual(result["ua"]["acbot.modules.example.greeting"], "Привіт")

    async def test_local_cache_unicode_and_dotted_module_names(self):
        from acbot._local_storage import LocalStorage, RemoteStorage
        with tempfile.TemporaryDirectory() as tmp:
            cache = LocalStorage.__new__(LocalStorage)
            cache._path = tmp
            cache.save("repo", "example", "# Українська\nvalue = 1\n")
            self.assertIn("Українська", cache.fetch("repo", "example"))
            cache.save("repo", "example", "value = 2\n")
            self.assertEqual(cache.fetch("repo", "example"), "value = 2\n")
        _, _, name = RemoteStorage._parse_url("https://github.com/hikariatama/host/raw/master/gg.gg.py")
        self.assertEqual(name, "gg.gg")
        with self.assertRaises(ValueError):
            RemoteStorage._parse_url("not-a-url")

    async def test_invalid_download_does_not_poison_cached_module(self):
        from acbot._local_storage import RemoteStorage
        storage = RemoteStorage.__new__(RemoteStorage)
        storage._local_storage = SimpleNamespace(fetch=Mock(return_value="value = 1"), save=Mock())
        response = SimpleNamespace(raise_for_status=Mock(), content=b"<html>Error</html>", text="<html>Error</html>")
        with patch("acbot._local_storage.requests.get", return_value=response):
            source = await storage.fetch("https://example.org/test.py")
        self.assertEqual(source, "value = 1")
        storage._local_storage.save.assert_not_called()

    async def test_database_recovers_previous_snapshot(self):
        from acbot.database import Database
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(SimpleNamespace(tg_id=1))
            db._db_file = Path(tmp) / "config-1.json"
            dict.update(db, {"module": {"value": "Привіт"}})
            self.assertTrue(db._save_local_atomic())
            db["module"]["value"] = "Updated"
            self.assertTrue(db._save_local_atomic())
            db._db_file.write_text("corrupt")
            db.clear()
            with self.assertLogs("acbot.database", level="WARNING"):
                db.read()
            self.assertEqual(db["module"]["value"], "Привіт")

    async def test_web_artwork_uses_local_files_and_requires_auth(self):
        from aiohttp.test_utils import TestClient, TestServer
        from acbot.web.core import Web
        with patch.dict(os.environ, {"AUTHORBOT_WEB_USER": "автор", "AUTHORBOT_WEB_PASSWORD": "пароль"}):
            app = Web(api_token=None, data_root=str(ROOT), connection=None, proxy=None)
        async with TestClient(TestServer(app.app)) as client:
            response = await client.get("/branding/bot.jpg")
            self.assertEqual(response.status, 401)
            auth = "Basic " + base64.b64encode("автор:пароль".encode()).decode()
            response = await client.get("/branding/bot.jpg", headers={"Authorization": auth})
            self.assertEqual(response.status, 200)
            self.assertTrue((await response.read()).startswith(b"\xff\xd8"))
            response = await client.get("/", headers={"Authorization": auth})
            self.assertEqual(response.status, 200)
            self.assertIn("/branding/bot.jpg", await response.text())
            bad_auth = "Basic " + base64.b64encode("автор:помилка".encode()).decode()
            response = await client.get("/", headers={"Authorization": bad_auth})
            self.assertEqual(response.status, 401)


if __name__ == "__main__":
    sys.argv = [sys.argv[0]]
    asyncio.run(import_all_modules())
    unittest.main(verbosity=2)
