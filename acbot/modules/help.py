# ©️ Dan G. && AuthorChe
# AGPL-3.0 · https://www.gnu.org/licenses/agpl-3.0.html

import difflib
import inspect
import math
import re
from html import unescape

from herokutl.tl.types import Message

from .. import loader, translations, utils
from ..public_pages import heading, buttons


@loader.tds
class Help(loader.Module):
    """Interactive help for installed modules and commands."""

    strings = {"name": "Help"}
    PAGE_SIZE = 8

    def __init__(self):
        # Preserve saved configuration of the former help renderer.
        self.config = loader.ModuleConfig(
            loader.ConfigValue("core_emoji", "🧩", lambda: "Core module bullet"),
            loader.ConfigValue("plain_emoji", "✦", lambda: "Custom module bullet"),
            loader.ConfigValue("empty_emoji", "◦", lambda: "Service module bullet"),
        )

    def _language(self):
        selected = self._db.get(translations.__name__, "lang", "en").split()
        return next((translations.normalize_language(lang) for lang in selected
                     if translations.normalize_language(lang) in translations.SUPPORTED_LANGUAGES), "en")

    @staticmethod
    def _name(module):
        try:
            return module.strings("name")
        except (KeyError, AttributeError, TypeError):
            return getattr(module, "name", module.__class__.__name__)

    def _module(self, query):
        query = query.strip().removeprefix(self.get_prefix())
        if module := self.lookup(query):
            return module, True
        command = self.allmodules.dispatch(query.lower())[1]
        if command:
            return command.__self__, True
        names = [self._name(mod) for mod in self.allmodules.modules]
        if closest := difflib.get_close_matches(query.lower(), [name.lower() for name in names], n=1, cutoff=0.45):
            return self.allmodules.modules[[name.lower() for name in names].index(closest[0])], False
        return None, False

    def find_aliases(self, command):
        func = self.allmodules.commands.get(command)
        return getattr(func, "aliases", None) or ([func.alias] if getattr(func, "alias", None) else [])

    async def _commands(self, module, message):
        return [(name, func) for name, func in getattr(module, "commands", {}).items()
                if await self.allmodules.check_security(message, func)]

    async def _inline_commands(self, module, user):
        return [(name, func) for name, func in getattr(module, "inline_handlers", {}).items()
                if await self.inline.check_inline_security(func=func, user=user)]

    async def _render(self, message, query="", page=0, force=False):
        esc = utils.escape_html
        language = self._language()
        title = self.strings("rich_title")
        rich = [heading("AuthorBot · " + title, "by AuthorChe")]
        classic = ["<b>AuthorBot · " + title + "</b>\n"]
        markup = []
        prefix = esc(self.get_prefix())
        if query:
            module, exact = self._module(query)
            if module is None:
                warning = self.strings("no_mod")
                rich += [f'<blockquote>{warning}</blockquote>']
                classic += [warning]
            else:
                name = esc(self._name(module))
                version = getattr(module, "__version__", None)
                if version:
                    name += " · v" + esc(".".join(map(str, version)))
                rich += [heading(name)]
                classic += [f'<b>{name}</b>']
                if doc := inspect.getdoc(module):
                    rich += [f'<p>{esc(doc)}</p>']
                    classic += [esc(doc)]
                if not exact:
                    rich += [f'<blockquote>{self.strings("not_exact")}</blockquote>']
                    classic += [self.strings("not_exact")]
                command_rows = []
                for name, func in sorted(await self._commands(module, message)):
                    aliases = self.find_aliases(name)
                    code = f'<code>{prefix}{esc(name)}</code>'
                    if aliases:
                        code += " · " + " · ".join(f'<code>{prefix}{esc(alias)}</code>' for alias in aliases)
                    doc = esc(inspect.getdoc(func)) if inspect.getdoc(func) else self.strings("undoc")
                    command_rows += [f'<tr><td>{code}</td><td>{doc}</td></tr>']
                    classic += [code + " — " + doc]
                for name, func in sorted(await self._inline_commands(module, message.sender_id)):
                    code = f'<code>@{esc(self.inline.bot_username)} {esc(name)}</code>'
                    doc = esc(inspect.getdoc(func)) if inspect.getdoc(func) else self.strings("undoc")
                    command_rows += [f'<tr><td>{code}</td><td>{doc}</td></tr>']
                    classic += [code + " — " + doc]
                if command_rows:
                    rich += ['<table bordered striped compact>' + ''.join(command_rows) + '</table>']
                else:
                    rich += [f'<p>{self.strings("rich_service")}</p>']
                    classic += [self.strings("rich_service")]
            markup += [[{"text": "◀ " + self.strings("rich_modules"), "callback": self._navigate, "args": (message, "", 0, force)}]]
        else:
            hidden = self.get("hide", [])
            modules = [mod for mod in self.allmodules.modules
                       if hasattr(mod, "commands") and (force or mod.__class__.__name__ not in hidden)]
            modules.sort(key=lambda mod: self._name(mod).casefold())
            pages = max(1, math.ceil(len(modules) / self.PAGE_SIZE))
            page = max(0, min(page, pages - 1))
            summary = self.strings("rich_summary").format(len(modules), len(hidden), prefix)
            rich += [f'<blockquote>{summary}</blockquote>']
            classic += [summary]
            rows = []
            cards = []
            for mod in modules[page * self.PAGE_SIZE:(page + 1) * self.PAGE_SIZE]:
                name = self._name(mod)
                commands = await self._commands(mod, message)
                inline_commands = await self._inline_commands(mod, message.sender_id)
                labels = [f'<code>{prefix}{esc(cmd)}</code>' for cmd, _ in commands]
                labels += [f'<code>@{esc(self.inline.bot_username)} {esc(cmd)}</code>' for cmd, _ in inline_commands]
                info = ' · '.join(labels) or self.strings("rich_service")
                icon = "🧩" if getattr(mod, "__origin__", "").startswith("<core") else "✦"
                rows += [f'<tr><td><b>{icon} {esc(name)}</b></td><td>{info}</td></tr>']
                classic += [f'<b>{esc(name)}</b>\n{info}']
                cards += [{"text": icon + " " + name, "callback": self._navigate, "args": (message, name, 0, force)}]
            rich += ['<table bordered striped compact>' + ''.join(rows) + '</table>']
            rich += [f'<p>{self.strings("rich_hint")}</p>']
            markup += utils.chunks(cards, 2)
            if pages > 1:
                navigation = []
                if page:
                    navigation += [{"text": "◀", "callback": self._navigate, "args": (message, "", page - 1, force)}]
                navigation += [{"text": f'{page + 1} / {pages}', "data": "empty"}]
                if page + 1 < pages:
                    navigation += [{"text": "▶", "callback": self._navigate, "args": (message, "", page + 1, force)}]
                markup += [navigation]
            loaded = self.lookup("Loader")
            if loaded and not getattr(loaded, "fully_loaded", True):
                rich += [f'<blockquote>{self.strings("partial_load")}</blockquote>']
                classic += [self.strings("partial_load")]
        markup += [[{"text": "✕ " + self.strings("rich_close"), "action": "close"}]]
        rich += ['<hr/>', buttons(language), '<footer>AuthorBot · by AuthorChe</footer>']
        # Classic Bot API cannot parse custom emoji tags from module language packs.
        classic = re.sub(r'</?emoji\b[^>]*>', '', '\n\n'.join(classic))
        if len(classic) > 3800:
            classic = esc(unescape(re.sub(r'<[^>]+>', '', classic))[:3500]) + '\n\n' + self.strings("rich_hint")
        html = re.sub(r'<emoji document_id=["\']?(\d+)["\']?>', r'<tg-emoji emoji-id="\1">', '\n'.join(rich)).replace('</emoji>', '</tg-emoji>')
        return html, classic, markup

    async def _navigate(self, call, message, query, page, force):
        await call.answer()
        html, classic, markup = await self._render(message, query, page, force)
        unit = self.inline._units.get(call.unit_id, {})
        old_keys = {button.get("_callback_data") for row in unit.get("buttons", []) for button in row}
        if not unit.get("rich_fallback"):
            try:
                target = ({"inline_message_id": call.inline_message_id}
                          if getattr(call, "inline_message_id", None)
                          else {"chat_id": call.chat_id, "message_id": call.message_id})
                await self.inline.rich.request(
                    "editMessageText", **target,
                    rich_message={"html": html}, reply_markup=self.inline.generate_markup(markup),
                )
                unit.update(rich_html=html, text=classic, buttons=markup)
                for key in old_keys:
                    self.inline._custom_map.pop(key, None)
                return
            except Exception:
                unit["rich_fallback"] = True
        if await call.edit(classic, reply_markup=markup):
            for key in old_keys:
                self.inline._custom_map.pop(key, None)

    async def modhelp(self, message: Message, args: str):
        await self._open(message, args)

    async def _open(self, message, query="", force=False):
        html, classic, markup = await self._render(message, query, force=force)
        await self.inline.form(
            message=message, text=classic, rich_html=html, reply_markup=markup,
            force_me=True, ttl=15 * 60,
        )

    @loader.command()
    async def help(self, message: Message):
        """[module or command] [-f] — open interactive Rich Message help."""
        args = utils.get_args_raw(message).strip()
        force = "-f" in args.split()
        args = " ".join(arg for arg in args.split() if arg != "-f")
        await self._open(message, args, force)

    @loader.command()
    async def helphide(self, message: Message):
        """<modules> — show or hide modules in the help catalog."""
        if not (modules := utils.get_args(message)):
            await utils.answer(message, self.strings("no_mod"))
            return
        hidden = self.get("hide", [])
        added, shown = [], []
        for name in modules:
            if not (module := self.lookup(name)):
                continue
            name = module.__class__.__name__
            if name in hidden:
                hidden.remove(name)
                shown += [name]
            else:
                hidden.append(name)
                added += [name]
        self.set("hide", hidden)
        await utils.answer(message, self.strings("hidden_shown").format(
            len(added), len(shown), "\n".join(map(utils.escape_html, added)), "\n".join(map(utils.escape_html, shown)),
        ))
