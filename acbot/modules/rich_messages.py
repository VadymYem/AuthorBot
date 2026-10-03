# ©️ AuthorChe
# Telegram Rich Message utilities for AuthorBot.

from herokutl.tl.types import Message

from .. import loader, utils
from ..inline.rich import RichMessageError
from ..public_pages import heading


@loader.tds
class RichMessagesMod(loader.Module):
    """Create and test Telegram Rich Messages through the AuthorBot inline bot."""

    strings = {
        "name": "RichMessages",
        "usage": (
            "<b>Rich Messages</b>\n"
            "<code>.richmsg &lt;Rich HTML&gt;</code>\n"
            "<code>.richmsg --md &lt;Rich Markdown&gt;</code>\n\n"
            "The result is sent to your private chat with the AuthorBot inline bot."
        ),
        "sent": "✅ <b>Rich Message sent through the inline bot.</b>",
        "error": "❌ <b>Rich Message error:</b> <code>{}</code>",
    }

    @loader.command()
    async def richmsg(self, message: Message):
        """<rich html> or --md <rich markdown> — send a Telegram Rich Message."""
        raw = utils.get_args_raw(message).strip()
        markdown = False

        if raw.startswith("--md "):
            markdown = True
            raw = raw[5:].strip()

        if not raw:
            reply = await message.get_reply_message()
            if reply and reply.raw_text:
                raw = reply.raw_text.strip()

        if not raw:
            await utils.answer(message, self.strings("usage"))
            return

        try:
            if markdown:
                await self.inline.rich.send(self._client.tg_id, markdown=raw)
            else:
                await self.inline.rich.send(self._client.tg_id, html=raw)
        except (RichMessageError, ValueError) as exc:
            await utils.answer(
                message,
                self.strings("error").format(utils.escape_html(str(exc))),
            )
            return

        await utils.answer(message, self.strings("sent"))

    @loader.command()
    async def richdemo(self, message: Message):
        """— send a showcase message with modern rich formatting."""
        demo = heading("AuthorBot · Rich Messages", "by AuthorChe") + """
<blockquote>Native Telegram Rich Messages are available to AuthorBot modules.</blockquote>
<table bordered striped compact>
<tr><th>Feature</th><th>Status</th></tr>
<tr><td>Headings and lists</td><td>✅</td></tr>
<tr><td>Tables</td><td>✅</td></tr>
<tr><td>Details blocks</td><td>✅</td></tr>
<tr><td>Rich buttons</td><td>✅</td></tr>
<tr><td>Media blocks</td><td>✅</td></tr>
</table>
<details><summary>Module API</summary><pre><code class="language-python">await self.inline.rich.send(
    chat_id,
    html="&lt;h1&gt;Hello&lt;/h1&gt;"
)</code></pre></details>
<tg-button-row align="center">
<tg-button type="url" style="primary" url="https://github.com/VadymYem/AuthorBot">AuthorBot</tg-button>
<tg-button type="url" url="https://authorche.top">AuthorChe</tg-button>
</tg-button-row>"""
        try:
            await self.inline.rich.send(self._client.tg_id, html=demo)
        except RichMessageError as exc:
            await utils.answer(
                message,
                self.strings("error").format(utils.escape_html(str(exc))),
            )
            return

        await utils.answer(message, self.strings("sent"))
