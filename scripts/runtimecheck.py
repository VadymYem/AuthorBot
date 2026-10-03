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
    def _inline_manager(self):
        from acbot.inline.core import InlineManager
        manager = InlineManager.__new__(InlineManager)
        manager._units = {"unit": {"chat": -100123, "message_id": 42,
                                  "inline_message_id": "encoded",
                                  "buttons": [[{"_callback_data": "close-key"}]]}}
        manager._custom_map = {"close-key": {"handler": Mock()}}
        manager._client = SimpleNamespace(delete_messages=AsyncMock())
        manager.bot = SimpleNamespace(delete_message=AsyncMock(), edit_message_reply_markup=AsyncMock())
        return manager

    async def test_close_uses_stored_message_ids_and_account_deletion(self):
        from acbot.inline.types import InlineMessage
        manager = self._inline_manager()
        manager.bot.delete_message.side_effect = RuntimeError("message can't be deleted")
        message = InlineMessage(manager, "unit", "encoded")
        call = SimpleNamespace(unit_id="unit", inline_message_id="encoded", answer=AsyncMock(), delete=message.delete)
        with patch("acbot.inline.utils.logger.warning") as warning:
            self.assertTrue(await manager._close_unit_handler(call))
        manager.bot.delete_message.assert_awaited_once_with(chat_id=-100123, message_id=42)
        manager._client.delete_messages.assert_awaited_once_with(-100123, [42])
        self.assertFalse(manager._units)
        self.assertFalse(manager._custom_map)
        manager.bot.edit_message_reply_markup.assert_not_awaited()
        warning.assert_not_called()

    async def test_close_detaches_inline_controls_without_false_warning(self):
        manager = self._inline_manager()
        call = SimpleNamespace(unit_id="unit", inline_message_id="encoded", answer=AsyncMock(), delete=AsyncMock(return_value=False))
        with patch("acbot.inline.utils.logger.warning") as warning:
            self.assertTrue(await manager._close_unit_handler(call))
        manager.bot.edit_message_reply_markup.assert_awaited_once_with(inline_message_id="encoded", reply_markup=None)
        self.assertFalse(manager._units)
        self.assertFalse(manager._custom_map)
        warning.assert_not_called()

    async def test_close_failure_preserves_controls_for_retry(self):
        manager = self._inline_manager()
        manager.bot.edit_message_reply_markup.side_effect = RuntimeError("temporarily offline")
        call = SimpleNamespace(unit_id="unit", inline_message_id="encoded", answer=AsyncMock(), delete=AsyncMock(return_value=False))
        with self.assertLogs("acbot.inline.utils", level="WARNING") as logs:
            self.assertFalse(await manager._close_unit_handler(call))
        self.assertIn("retry", logs.output[0])
        self.assertIn("unit", manager._units)
        self.assertIn("close-key", manager._custom_map)

    async def test_close_is_idempotent_when_message_is_already_deleted(self):
        manager = self._inline_manager()
        manager.bot.delete_message.side_effect = RuntimeError("Bad Request: message to delete not found")
        self.assertTrue(await manager._delete_unit_message(unit_id="unit", chat_id=-100123, message_id=42))
        self.assertTrue(await manager._delete_unit_message(chat_id=-100123, message_id=42))
        manager._client.delete_messages.assert_not_awaited()
        self.assertFalse(manager._units)
        self.assertFalse(manager._custom_map)

    async def test_unload_cleans_callbacks_even_when_module_cleanup_fails(self):
        manager = self._inline_manager()
        manager._units["unit"]["on_unload"] = AsyncMock(side_effect=RuntimeError("cleanup failed"))
        self.assertTrue(await manager._unload_unit("unit"))
        self.assertFalse(manager._units)
        self.assertFalse(manager._custom_map)

    async def test_inline_rich_form_and_classic_fallback_keep_controls(self):
        manager = self._inline_manager()
        manager._units["unit"].update(type="form", uid="unit", rich_html="<aside><b>AuthorBot</b></aside>",
                                     text="<b>AuthorBot</b>", buttons=[[{"text": "Close", "action": "close"}]])
        manager.rich = SimpleNamespace(request=AsyncMock())
        query = SimpleNamespace(id="query-id", query="unit", answer=AsyncMock())
        await manager._form_inline_handler(query)
        kwargs = manager.rich.request.call_args.kwargs
        self.assertIn("rich_message", kwargs["results"][0]["input_message_content"])
        self.assertIn("callback_data", kwargs["results"][0]["reply_markup"].to_python()["inline_keyboard"][0][0])
        query.answer.assert_not_awaited()
        manager.rich.request.side_effect = RuntimeError("unsupported rich message")
        await manager._form_inline_handler(query)
        result = query.answer.call_args.args[0][0].to_python()
        self.assertEqual(result["input_message_content"]["message_text"], "<b>AuthorBot</b>")
        self.assertTrue(result["reply_markup"]["inline_keyboard"])
        self.assertTrue(manager._units["unit"]["rich_fallback"])

    async def test_inline_forbidden_returns_cleanly_without_waiting_for_chosen_result(self):
        from herokutl.errors import ChatSendInlineForbiddenError
        manager = self._inline_manager()
        manager._units.clear()
        manager._find_caller_sec_map = Mock(return_value=None)
        manager._invoke_unit = AsyncMock(side_effect=ChatSendInlineForbiddenError(request=None))
        manager._client.send_message = AsyncMock()
        manager.translator = SimpleNamespace(getkey=lambda key: key)
        self.assertFalse(await asyncio.wait_for(manager.form("<b>AuthorBot</b>", 123, ttl=30), 1))
        self.assertFalse(manager._units)
        manager._client.send_message.assert_awaited_once_with(123, "inline.inline403")

    def _module_strings(self, mod, language="en"):
        from acbot import translations
        data = translations.translator.data[language]
        mod._db = SimpleNamespace(get=lambda section, key, default=None: language if key == "lang" else default)
        translator = SimpleNamespace(db=mod._db, getkey=lambda key: data.get(key.removeprefix("acbot.modules.")))
        mod.strings = translations.Strings(mod, translator)

    async def test_help_pagination_respects_security_and_opens_rich_form(self):
        from acbot.modules.help import Help
        mod = Help()
        self._module_strings(mod, "de")
        mod.get_prefix = lambda: "."
        mod.lookup = lambda query: None
        modules = [SimpleNamespace(strings=lambda key, i=i: f"Module{i:02}", commands={"visible": Mock(), "secret": Mock()},
                                   inline_handlers={}, __origin__="<core>") for i in range(10)]
        denied = {item.commands["secret"] for item in modules}
        mod.allmodules = SimpleNamespace(modules=modules, check_security=AsyncMock(side_effect=lambda message, func: func not in denied))
        mod.inline = SimpleNamespace(bot_username="author_bot", check_inline_security=AsyncMock(return_value=True), form=AsyncMock())
        message = SimpleNamespace(sender_id=123)
        html, classic, markup = await mod._render(message, force=True)
        self.assertIn("<aside>", html)
        self.assertIn("<table", html)
        self.assertIn("AuthorChe", html)
        self.assertNotIn("secret", html)
        self.assertIn("Module07", html)
        self.assertNotIn("Module08", html)
        self.assertTrue(any(button.get("text") == "1 / 2" for row in markup for button in row))
        html, _, _ = await mod._render(message, page=1)
        self.assertIn("Module08", html)
        self.assertNotIn("Module00", html)
        await mod._open(message)
        self.assertIn("rich_html", mod.inline.form.call_args.kwargs)
        self.assertEqual(mod.inline.form.call_args.kwargs["ttl"], 900)

    async def test_help_module_details_and_navigation_fallback(self):
        from acbot.modules.help import Help
        mod = Help()
        self._module_strings(mod)
        mod.get_prefix = lambda: "."
        async def visible(message):
            """Helpful command description."""
        visible.aliases = ["shortcut"]
        target = SimpleNamespace(strings=lambda key: "Example", commands={"visible": visible}, inline_handlers={}, __version__=(1, 2, 3, 4))
        mod.lookup = lambda query: target if query == "Example" else None
        mod.allmodules = SimpleNamespace(modules=[target], commands={"visible": visible}, check_security=AsyncMock(return_value=True))
        mod.inline = SimpleNamespace(bot_username="author_bot", check_inline_security=AsyncMock(return_value=True),
                                     _units={"unit": {"buttons": [[{"_callback_data": "old"}]]}}, _custom_map={"old": {}},
                                     generate_markup=lambda markup: markup, rich=SimpleNamespace(request=AsyncMock()))
        message = SimpleNamespace(sender_id=123)
        html, _, _ = await mod._render(message, query="Example")
        self.assertIn("Helpful command description.", html)
        self.assertIn(".shortcut", html)
        self.assertIn("v1.2.3.4", html)
        call = SimpleNamespace(unit_id="unit", inline_message_id="encoded", answer=AsyncMock(), edit=AsyncMock(return_value=True))
        await mod._navigate(call, message, "Example", 0, False)
        self.assertIn("rich_message", mod.inline.rich.request.call_args.kwargs)
        self.assertFalse(mod.inline._custom_map)
        mod.inline.rich.request.side_effect = RuntimeError("rich edit unsupported")
        await mod._navigate(call, message, "Example", 0, False)
        call.edit.assert_awaited_once()
        self.assertTrue(mod.inline._units["unit"]["rich_fallback"])

    async def test_random_tools_reject_invalid_bounds_and_escape_options(self):
        from acbot.modules.InlineRandom import InlineRandomMod
        mod = InlineRandomMod()
        self._module_strings(mod, "ua")
        for args in ("0", "-1", "²", "9" * 13, "not a number"):
            self.assertIsNone(await mod.random_inline_handler(SimpleNamespace(args=args)))
        result = await mod.random_inline_handler(SimpleNamespace(args="1"))
        self.assertIn("<code>1</code>", result["message"])
        self.assertIsNone(await mod.choice_inline_handler(SimpleNamespace(args=",,one,,")))
        result = await mod.choice_inline_handler(SimpleNamespace(args="<b>A</b>, <i>B</i>"))
        self.assertIn("&lt;", result["message"])

    async def test_weather_uses_selected_language_and_longread_escapes_text(self):
        from acbot.modules.Weather import WeatherMod
        from acbot.modules.LongRead import LongReadMod
        mod = WeatherMod()
        self._module_strings(mod, "ua")
        response = SimpleNamespace(raise_for_status=Mock(), text="\033[31mForecast")
        with patch("acbot.modules.Weather.utils.run_sync", AsyncMock(return_value=response)) as fetch:
            self.assertEqual(await mod._fetch("Berlin"), "Forecast")
            self.assertIn("lang=uk", fetch.call_args.args[1])
            await mod._fetch("Berlin", compact=True)
            self.assertIn("format=3&lang=uk", fetch.call_args.args[1])
        longread = LongReadMod()
        call = SimpleNamespace(edit=AsyncMock(), answer=AsyncMock())
        await longread._handler(call, "<b>Hello & goodbye</b>")
        call.edit.assert_awaited_once_with("&lt;b&gt;Hello &amp; goodbye&lt;/b&gt;")

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
        mod._public_rich = lambda page, language: START_RICH
        mod.inline = SimpleNamespace(rich=SimpleNamespace(send=AsyncMock()))
        message = SimpleNamespace(chat=SimpleNamespace(id=123), answer=AsyncMock())
        mod._language = lambda *args: "ua"
        mod.get_prefix = lambda: "."
        await mod._send_public_page(message, "start")
        payload = mod.inline.rich.send.call_args.kwargs
        self.assertIn("tg://photo?id=bot_artwork", payload["html"])
        self.assertTrue(payload["files"]["bot_artwork"].is_file())
        self.assertEqual(payload["media"][0]["media"]["media"], "attach://bot_artwork")
        message.answer.assert_not_awaited()

    async def test_public_page_fallback_remains_available(self):
        from acbot.modules.inline_stuff import InlineStuff, START_RICH
        mod = InlineStuff()
        mod._public_rich = lambda page, language: START_RICH
        mod.inline = SimpleNamespace(rich=SimpleNamespace(send=AsyncMock(side_effect=RuntimeError("offline"))))
        message = SimpleNamespace(chat=SimpleNamespace(id=123), answer=AsyncMock())
        mod._language = lambda *args: "ua"
        mod.get_prefix = lambda: "."
        with self.assertLogs("acbot.modules.inline_stuff", level="WARNING"):
            await mod._send_public_page(message, "start")
        message.answer.assert_awaited_once()

    async def test_dialog_filters_wrapper_and_plain_list(self):
        from acbot.modules.updater import UpdaterMod
        from herokutl.tl.types import DialogFilter, TextWithEntities
        from herokutl.tl.types.messages import DialogFilters
        from herokutl.tl.functions.messages import UpdateDialogFilterRequest

        existing = DialogFilter(2, TextWithEntities("acbot", []), [], [], [])
        for response in ([existing], DialogFilters([existing])):
            mod = UpdaterMod()
            mod._client = AsyncMock(return_value=response)
            self.assertTrue(await mod._add_folder())
            mod._client.assert_awaited_once()

        mod = UpdaterMod()
        calls = []
        async def request(value):
            calls.append(value)
            return DialogFilters([]) if len(calls) == 1 else True
        async def dialogs(*args, **kwargs):
            if False:
                yield
        mod._client = SimpleNamespace()
        class Client:
            loader = SimpleNamespace(inline=SimpleNamespace(init_complete=False))
            iter_dialogs = staticmethod(dialogs)
            __call__ = staticmethod(request)
        mod._client = Client()
        self.assertTrue(await mod._add_folder())
        self.assertIsInstance(calls[1], UpdateDialogFilterRequest)
        self.assertEqual(calls[1].filter.title.text, "AuthorBot")
        self.assertTrue(bytes(calls[1]))  # Serialize with the installed real TL schema.

    async def test_optional_reaction_limit_is_not_retried_or_marked_sent(self):
        from acbot.modules.quickstart import Quickstart
        mod = Quickstart()
        saved = {}
        mod.get = lambda key, default=None: saved.get(key, default)
        mod.set = lambda key, value: saved.update({key: value})
        class Client:
            get_input_entity = AsyncMock(return_value="channel")
            __call__ = AsyncMock(side_effect=RuntimeError("CUSTOM_REACTIONS_TOO_MANY"))
        mod._client = Client()
        await mod._apply_support_reactions()
        self.assertEqual(saved["support_reactions_skipped"], [9, 17, 18, 36])
        self.assertNotIn("support_reactions_done", saved)
        await mod._apply_support_reactions()
        self.assertEqual(mod._client.__call__.await_count, 4)

    async def test_retired_catalog_is_absent_from_modules_and_presets(self):
        from acbot.modules.presets import PRESETS
        self.assertFalse((ROOT / "acbot/modules/unit_heta.py").exists())
        self.assertTrue(all(urls for urls in PRESETS.values()))
        self.assertTrue(all("heta.dan.tatar" not in url for urls in PRESETS.values() for url in urls))

    async def test_personal_bot_name_is_safe_and_bounded(self):
        from acbot.branding import personal_bot_name
        self.assertEqual(personal_bot_name("Vadym Yemelianov"), "AuthorBot of Vadym Yemelianov")
        self.assertEqual(personal_bot_name("  Іван\nПетренко  "), "AuthorBot of Іван Петренко")
        self.assertEqual(personal_bot_name(""), "AuthorBot of User")
        self.assertEqual(len(personal_bot_name("a" * 200)), 64)
        self.assertIn("山田", personal_bot_name("山田 太郎"))

    async def test_localized_public_pages_and_language_selection(self):
        from acbot import translations
        from acbot.public_pages import rich_page, fallback_page, PAGES, bot_commands
        from acbot.modules.inline_stuff import InlineStuff, LEGACY_DEFAULTS
        from bs4 import BeautifulSoup
        from ruamel.yaml import YAML
        from string import Formatter

        base = YAML(typ="safe").load(ROOT / "acbot/langpacks/en.yml")
        for language in translations.SUPPORTED_LANGUAGES:
            pack = YAML(typ="safe").load(ROOT / f"acbot/langpacks/{language}.yml")
            self.assertEqual(set(pack["$public_pages"]), set(base["$public_pages"]))
            for page in (*PAGES, "welcome"):
                html = rich_page(page, language, prefix="!")
                soup = BeautifulSoup(html, "html.parser")
                self.assertEqual(soup.aside.b.text, "AuthorBot" if page in {"start", "about", "welcome"} else pack["$public_pages"][page + "_label"])
                self.assertIn("AuthorChe", html)
                self.assertNotIn("Author C", html)
                self.assertTrue(all(row.get("align") == "center" for row in soup.find_all("tg-button-row")))
                fallback = BeautifulSoup(fallback_page(page, language), "html.parser")
                self.assertFalse(fallback.find(["aside", "table", "figure", "details", "tg-button"]))
            self.assertIn("author", [cmd["command"] for cmd in bot_commands(language)])
        for language in ("de", "ja"):
            pack = YAML(typ="safe").load(ROOT / f"acbot/langpacks/{language}.yml")
            for module, strings in base.items():
                for key, value in strings.items():
                    translated = pack[module][key]
                    fields = lambda s: [(field, conv) for _, field, _, conv in Formatter().parse(s) if field is not None]
                    self.assertEqual(fields(value), fields(translated), (language, module, key))
        mod = InlineStuff()
        mod._db = SimpleNamespace(get=lambda *args: "ua")
        visitor = SimpleNamespace(from_user=SimpleNamespace(language_code="de-DE"))
        self.assertEqual(mod._language(visitor), "de")
        self.assertEqual(mod._language(visitor, "uk"), "ua")
        self.assertEqual(translations.normalize_language("jp"), "ja")
        self.assertIn("Deutsch", translations.SUPPORTED_LANGUAGES["de"])
        mod.get_prefix = lambda: "."
        mod.get = lambda *args: '<h1>Custom page</h1>'
        self.assertEqual(mod._public_rich("about", "de"), '<h1>Custom page</h1>')

    async def test_quickstart_rich_and_classic_delivery(self):
        from acbot.modules.quickstart import Quickstart
        mod = Quickstart()
        mod._client = SimpleNamespace(tg_id=123)
        mod._db = SimpleNamespace(get=lambda *args: "de")
        mod.get_prefix = lambda: "!"
        mod.mark = lambda: []
        mod.text = lambda: "Fallback"
        mod.inline = SimpleNamespace(generate_markup=lambda value: value,
                                     rich=SimpleNamespace(send=AsyncMock()),
                                     bot=SimpleNamespace(send_message=AsyncMock()))
        await mod._send_welcome()
        payload = mod.inline.rich.send.call_args.kwargs
        self.assertIn("!help", payload["html"])
        self.assertIn("Dein Telegram", payload["html"])
        self.assertTrue(payload["files"]["bot_artwork"].is_file())
        mod.inline.bot.send_message.assert_not_awaited()
        mod.inline.rich.send.side_effect = RuntimeError("unsupported")
        await mod._send_welcome()
        mod.inline.bot.send_message.assert_awaited_once()

    async def test_public_author_aliases_and_editor_permissions(self):
        from acbot.modules.inline_stuff import InlineStuff
        mod = InlineStuff()
        mod._send_public_page = AsyncMock()
        for command in ("/author", "/автор", "/aboutauthor", "/author@companion_bot"):
            message = SimpleNamespace(text=command + " de")
            await mod.aiogram_watcher(message)
            mod._send_public_page.assert_awaited_with(message, "author", "de")
        mod.set = Mock()
        message = SimpleNamespace(from_user=SimpleNamespace(id=1), answer=AsyncMock())
        await mod._set_public_page(message, "author", "<h1>Unsafe edit</h1>")
        mod.set.assert_not_called()
        message.from_user.id = 6316376597
        await mod._set_public_page(message, "author", "reset")
        mod.set.assert_called_once_with("public_author_rich", None)

    async def test_running_banner_clears_before_ascii_and_status(self):
        import io
        from acbot._internal import print_running_banner
        output = io.StringIO()
        output.isatty = lambda: True
        def clear(*args, **kwargs):
            self.assertEqual(args[0], ["clear"])
            output.write("<CLEAR>")
            return SimpleNamespace(returncode=0)
        with patch("sys.stdout", output), patch("acbot._internal.subprocess.run", side_effect=clear):
            print_running_banner("123456789", "1.10.11", False, "ua")
        rendered = output.getvalue()
        self.assertTrue(rendered.startswith("<CLEAR>"))
        self.assertIn("|____/", rendered)
        self.assertIn("AuthorChe", rendered)
        self.assertIn("ЗАПУЩЕНО", rendered)
        self.assertIn("1.10.11", rendered)
        self.assertIn("1234567", rendered)

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
