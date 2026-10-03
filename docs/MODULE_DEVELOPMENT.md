# AuthorBot Module Development

Цей документ є wiki-ready довідником для розробки модулів AuthorBot.

## 1. Мінімальний модуль

```python
from herokutl.tl.types import Message

from .. import loader, utils


@loader.tds
class HelloWorldMod(loader.Module):
    """A small, complete AuthorBot module."""

    strings = {
        "name": "HelloWorld",
        "hello": "👋 <b>Hello from AuthorBot!</b>",
    }

    @loader.command()
    async def hello(self, message: Message):
        """— send a test message."""
        await utils.answer(message, self.strings("hello"))
```

## 2. Configuration

```python
from herokutl.tl.types import Message

from .. import loader, utils


@loader.tds
class ConfigExampleMod(loader.Module):
    strings = {"name": "ConfigExample"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                True,
                "Enable the module",
                validator=loader.validators.Boolean(),
            ),
        )

    @loader.command()
    async def configexample(self, message: Message):
        if not self.config["enabled"]:
            await utils.answer(message, "Module is disabled.")
            return
        await utils.answer(message, "<b>Configuration works.</b>")
```

## 3. Persistent module data

```python
count = self.get("count", 0)
self.set("count", count + 1)
```

Або:

```python
self._db.set("MyModule", "enabled", True)
value = self._db.get("MyModule", "enabled", False)
```

## 4. Public inline handler

```python
from .. import loader
from ..inline.types import InlineQuery


@loader.tds
class PublicInlineMod(loader.Module):
    strings = {"name": "PublicInline"}

    @loader.inline_everyone
    async def hello_inline_handler(self, query: InlineQuery) -> dict:
        return {
            "title": "AuthorBot",
            "description": "Public inline example",
            "message": "<b>Hello from a public inline command.</b>",
            "thumb": "https://raw.githubusercontent.com/VadymYem/AuthorBot/main/assets/bot_pfp.jpg",
        }
```

Не використовуйте `inline_everyone` для команд, що читають приватні чати, файли, токени, Saved Messages або виконують системні дії.

## 5. Callback buttons

```python
from herokutl.tl.types import Message

from .. import loader
from ..inline.types import InlineCall


@loader.tds
class CallbackDemoMod(loader.Module):
    strings = {"name": "CallbackDemo"}

    @loader.command()
    async def callbackdemo(self, message: Message):
        await self.inline.form(
            message=message,
            text="<b>Callback demo</b>",
            reply_markup=[[
                {"text": "Update", "callback": self._update},
                {"text": "Close", "action": "close"},
            ]],
        )

    async def _update(self, call: InlineCall):
        await call.answer("Updated")
        await call.edit("<b>Updated successfully.</b>")
```

## 6. Telegram Rich Messages

### Rich HTML

```python
from herokutl.tl.types import Message

from .. import loader, utils


@loader.tds
class RichExampleMod(loader.Module):
    strings = {"name": "RichExample"}

    @loader.command()
    async def richcard(self, message: Message):
        rich_html = """<h1>AuthorBot</h1>
<blockquote>Structured Telegram Rich Message.</blockquote>
<table bordered striped compact>
<tr><th>Feature</th><th>Status</th></tr>
<tr><td>Tables</td><td>✅</td></tr>
<tr><td>Details</td><td>✅</td></tr>
<tr><td>Buttons</td><td>✅</td></tr>
</table>
<details><summary>More</summary>Rich HTML is rendered by Telegram.</details>
<tg-button-row align="center">
<tg-button type="url" style="primary" url="https://github.com/VadymYem/AuthorBot">GitHub</tg-button>
</tg-button-row>"""

        await self.inline.rich.send(self._client.tg_id, html=rich_html)
        await utils.answer(message, "✅ Rich Message sent.")
```

### Rich Markdown

```python
await self.inline.rich.send(
    self._client.tg_id,
    markdown="# AuthorBot\n\n**Rich Markdown** is enabled.",
)
```

### Streaming draft

```python
await self.inline.rich.draft(
    self._client.tg_id,
    101,
    html="<tg-thinking>Generating…</tg-thinking>",
    can_stop=True,
    keep_on_stop=True,
)
```

Після draft надішліть фінальний persistent message через `sendRichMessage`.

### Raw Bot API

```python
result = await self.inline.rich.request("getMe")
```

## 7. Watchers

```python
from .. import loader


@loader.tds
class WatcherExampleMod(loader.Module):
    strings = {"name": "WatcherExample"}

    @loader.watcher("in")
    async def watcher(self, message):
        if message.raw_text == "ping":
            await message.reply("pong")
```

## 8. HTTP requests

Завжди встановлюйте timeout і перевіряйте status.

```python
import aiohttp

timeout = aiohttp.ClientTimeout(total=20)
async with aiohttp.ClientSession(timeout=timeout) as session:
    async with session.get("https://authorche.top") as response:
        response.raise_for_status()
        text = await response.text()
```

## 9. Cleanup

```python
import asyncio

from .. import loader


@loader.tds
class LifecycleExampleMod(loader.Module):
    strings = {"name": "LifecycleExample"}

    async def client_ready(self):
        self._task = asyncio.create_task(self._worker())

    async def _worker(self):
        while True:
            await asyncio.sleep(60)

    async def on_unload(self):
        self._task.cancel()
```

## 10. Security checklist

1. Немає hardcoded token/API key/session string.
2. Public handler не читає приватні дані.
3. HTTP має timeout та перевірку status code.
4. Файлові шляхи не дозволяють path traversal.
5. Shell-команди не будуються з raw user input.
6. Callback має security policy.
7. Tasks закриваються в `on_unload`.
8. DB містить лише JSON-serializable values.
9. Модуль не додає сторонніх ID до owner/security list.
10. Помилки не виводять secrets у logs.

## 11. Module repository format

Primary repository AuthorBot:

```text
https://github.com/hikariatama/host/raw/master
```

Repository повинен мати `full.txt`. Кожний непорожній рядок — basename Python-модуля без `.py`.

## 12. Compatibility

Для Rich Messages використовуйте `self.inline.rich`, а не приватні internals aiogram 2.x.
