
#              Ā© Copyright 2022
#           https://t.me/AuthorChe
# š      Licensed under the GNU AGPLv3
# š https://www.gnu.org/licenses/agpl-3.0.html

# meta developer: @Vadym_Yem | @hikariatama
	
import difflib
import inspect
import logging

from ..inline.types import InlineCall
from telethon.tl.types import Message

from .. import loader, security, utils

logger = logging.getLogger(__name__)


@loader.tds
class HelpMod(loader.Module):
    """Help module"""

    strings = {
        "name": "Help",
        "bad_module": "<b>š« <b>Module</b> <code>{}</code> <b>not found</b>",
        "single_mod_header": (
            "<emoji document_id='6318565919471699564'>š</emoji> <b>{}</b>:"
        ),
        "single_cmd": "\nā«ļø <code>{}{}</code> {}",
        "undoc_cmd": "š¦„ No docs",
        "all_header": (
            "<emoji document_id='6318565919471699564'>š</emoji> <b>{} mods available,"
            " {} hidden:</b>"
        ),
        "mod_tmpl": "\n{} <code>{}</code>",
        "first_cmd_tmpl": ": [ {}",
        "cmd_tmpl": " | {}",
        "no_mod": "š« <b>Specify module to hide</b>",
        "hidden_shown": (
            "<emoji document_id='6318565919471699564'>š</emoji> <b>{} modules hidden,"
            " {} modules shown:</b>\n{}\n{}"
        ),
        "ihandler": "\nš¹ <code>{}</code> {}",
        "undoc_ihandler": "š¦„ No docs",
        "joined": (
            "<emoji document_id='6318565919471699564'>š</emoji> <b>Joined the</b> <a"
            " href='https://t.me/AuthorChe'>AuthorChe'sā</a>"
        ),
        "join": (
            "<emoji document_id='6318565919471699564'>š</emoji> <b>Join the</b> <a"
            " href='https://t.me/AuthorChe'>AuthorChe'sā</a>"
        ),
        "partial_load": (
            "<emoji document_id='5370740716840425754'>āļø</emoji> <b>AuthorChe's is not"
            " fully loaded, so not all functions are shown</b>"
        ),
        "not_exact": (
            "<emoji document_id='5370740716840425754'>āļø</emoji> <b>No exact match"
            " occured, so the closest result is shown instead</b>"
        ),
    }

    strings_ua = {
        "bad_module": "<b>š« <b>ŠŠ¾Š“ŃŠ»Ń</b> <code>{}</code> <b>Š½Šµ Š·Š½Š°Š¹Š“ŠµŠ½Š¾</b>",
        "single_mod_header": (
            "<emoji document_id='6318565919471699564'>š</emoji> <b>{}</b>:"
        ),
        "single_cmd": "\nā«ļø <code>{}{}</code> {}",
        "undoc_cmd": "š¦„ ŠŠµŠ¼Š°Ń Š¾ŠæŠøŃŃ",
        "all_header": (
            "<emoji document_id='6318565919471699564'>š</emoji> <b>{} ŠŗŠ¾Š¼Š°Š½Š“ Š²ŃŠ“ŠŗŃŠøŃŠ¾,"
            " {} ŠæŃŠøŃŠ¾Š²Š°Š½Š¾:</b>"
        ),
        "mod_tmpl": "\n{} <code>{}</code>",
        "first_cmd_tmpl": ": [ {}",
        "cmd_tmpl": " | {}",
        "no_mod": "š« <b>ŠŠŗŠ°Š¶Šø Š¼Š¾Š“ŃŠ»Ń(-Ń), ŃŠŗŃ ŠæŠ¾ŃŃŃŠ±Š½Š¾ ŠæŃŠøŃŠ¾Š²Š¾ŃŠø</b>",
        "hidden_shown": (
            "<emoji document_id='6318565919471699564'>š</emoji> <b>{} ŠŗŠ¾Š¼Š°Š½Š“ ŠæŃŠøŃŠ¾Š²Š°Š½Š¾,"
            " {} Š¼Š¾Š“ŃŠ»ŃŠ² ŠæŠ¾ŠŗŠ°Š·Š°Š½Š¾:</b>\n{}\n{}"
        ),
        "ihandler": "\nš¹ <code>{}</code> {}",
        "undoc_ihandler": "š¦„ ŠŠµŠ¼Š°Ń Š¾ŠæŠøŃŃ",
        "joined": (
            "š <b>ŠŃŠøŃŠ“Š½Š°Š²ŃŃ Š²</b> <a href='https://t.me/AuthorChe'>AuthorChe'sā</a>"
        ),
        "join": "š <b>ŠŃŠøŃŠ“Š½ŃŠ¹ŃŃ Š²</b> <a href='https://t.me/AuthorChe'>AuthorChe'sā</a>",
        "_cls_doc": "ŠŠ¾Š“ŃŠ»Ń Š“Š¾ŠæŠ¾Š¼Š¾Š³Šø(ŃŠæŠµŃŃŠ°Š»ŃŠ½Š¾ Š“Š»Ń acbot)",
        "partial_load": (
            "<emoji document_id='5370740716840425754'>āļø</emoji> <b>AuthorChe's ŃŠµ Š½Šµ"
            " Š·Š°Š²Š°Š½ŃŠ°Š¶ŠøŠ²ŃŃ ŠæŠ¾Š²Š½ŃŃŃŃ, ŃŠ¾Š¼Ń ŠæŠ¾ŠŗŠ°Š·Š°Š½Š¾ Š½Šµ Š²ŃŃ ŃŃŠ½ŠŗŃŃŃ</b>"
        ),
        "not_exact": (
            "<emoji document_id='5370740716840425754'>āļø</emoji> <b>Š¢Š¾ŃŠ½Š¾Š³Š¾ ŃŠæŃŠ²ŠæŠ°Š“ŃŠ½Š½Ń"
            " Š½Šµ Š·Š½Š°ŃŠ»Š¾ŃŃ, ŃŠ¾Š¼Ń Š±ŃŠ»Š¾ Š²ŠøŠ±ŃŠ°Š½Š¾ Š½Š°Š¹Š±ŃŠ»ŃŃ ŃŃŠ¾Š¶Šµ</b>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "core_emoji",
                "āŖļø",
                lambda: "Core module bullet",
                validator=loader.validators.String(length=1),
            ),
            loader.ConfigValue(
                "acbot_emoji",
                "ā",
                lambda: "acbot-only module bullet",
                validator=loader.validators.String(length=1),
            ),
            loader.ConfigValue(
                "plain_emoji",
                "ā«ļø",
                lambda: "Plain module bullet",
                validator=loader.validators.String(length=1),
            ),
            loader.ConfigValue(
                "empty_emoji",
                "šāšØ",
                lambda: "Empty modules bullet",
                validator=loader.validators.String(length=1),
            ),
        )

    @loader.command(
        ua_doc=(
            "<Š¼Š¾Š“ŃŠ»Ń ŃŠø Š¼Š¾Š“ŃŠ»Ń> - Š”ŃŠ¾Š²Š°ŃŠø Š¼Š¾Š“ŃŠ»Ń(-Ń) Š· Š¼ŠµŠ½Ń Š“Š¾ŠæŠ¾Š¼Š¾Š³Šø\n*Š Š¾Š·Š“ŃŠ»ŃŠ¹ Š¼Š¾Š“ŃŠ»Ń"
            " ŠæŃŠ¾Š±ŃŠ»Š°Š¼Šø"
        )
    )
    async def helphide(self, message: Message):
        """<module or modules> - Hide module(-s) from help
        *Split modules by spaces"""
        modules = utils.get_args(message)
        if not modules:
            await utils.answer(message, self.strings("no_mod"))
            return

        mods = [
            i.strings["name"]
            for i in self.allmodules.modules
            if hasattr(i, "strings") and "name" in i.strings
        ]

        modules = list(filter(lambda module: module in mods, modules))
        currently_hidden = self.get("hide", [])
        hidden, shown = [], []
        for module in modules:
            if module in currently_hidden:
                currently_hidden.remove(module)
                shown += [module]
            else:
                currently_hidden += [module]
                hidden += [module]

        self.set("hide", currently_hidden)

        await utils.answer(
            message,
            self.strings("hidden_shown").format(
                len(hidden),
                len(shown),
                "\n".join([f"šāšØ <i>{m}</i>" for m in hidden]),
                "\n".join([f"š <i>{m}</i>" for m in shown]),
            ),
        )

    async def modhelp(self, message: Message, args: str):
        exact = True
        module = self.lookup(args)

        if not module:
            _args = args.lower()
            _args = _args[1:] if _args.startswith(self.get_prefix()) else _args
            if _args in self.allmodules.commands:
                module = self.allmodules.commands[_args].__self__

        if not module:
            module = self.lookup(
                next(
                    (
                        reversed(
                            sorted(
                                [
                                    module.strings["name"]
                                    for module in self.allmodules.modules
                                ],
                                key=lambda x: difflib.SequenceMatcher(
                                    None,
                                    args.lower(),
                                    x,
                                ).ratio(),
                            )
                        )
                    ),
                    None,
                )
            )

            exact = False

        try:
            name = module.strings("name")
        except KeyError:
            name = getattr(module, "name", "ERROR")

        _name = (
            f"{utils.escape_html(name)} (v{module.__version__[0]}.{module.__version__[1]}.{module.__version__[2]})"
            if hasattr(module, "__version__")
            else utils.escape_html(name)
        )

        reply = self.strings("single_mod_header").format(_name)
        if module.__doc__:
            reply += "<i>\nā¹ļø " + utils.escape_html(inspect.getdoc(module)) + "\n</i>"

        commands = {
            name: func
            for name, func in module.commands.items()
            if await self.allmodules.check_security(message, func)
        }

        if hasattr(module, "inline_handlers"):
            for name, fun in module.inline_handlers.items():
                reply += self.strings("ihandler").format(
                    f"@{self.inline.bot_username} {name}",
                    (
                        utils.escape_html(inspect.getdoc(fun))
                        if fun.__doc__
                        else self.strings("undoc_ihandler")
                    ),
                )

        for name, fun in commands.items():
            reply += self.strings("single_cmd").format(
                self.get_prefix(),
                name,
                (
                    utils.escape_html(inspect.getdoc(fun))
                    if fun.__doc__
                    else self.strings("undoc_cmd")
                ),
            )

        await utils.answer(
            message, f"{reply}\n\n{'' if exact else self.strings('not_exact')}"
        )

    @loader.unrestricted
    @loader.command(ua_doc="[Š¼Š¾Š“ŃŠ»Ń] [-f] - ŠŠ¾ŠŗŠ°Š·Š°ŃŠø Š¼ŠµŠ½Ń Š“Š¾ŠæŠ¾Š¼Š¾Š³Šø")
    async def help(self, message: Message):
        """[module] [-f] - Show help"""
        args = utils.get_args_raw(message)
        force = False
        if "-f" in args:
            args = args.replace(" -f", "").replace("-f", "")
            force = True

        if args:
            await self.modhelp(message, args)
            return

        count = 0
        for i in self.allmodules.modules:
            try:
                if i.commands or i.inline_handlers:
                    count += 1
            except Exception:
                pass

        hidden = self.get("hide", [])

        reply = self.strings("all_header").format(count, 0 if force else len(hidden))
        shown_warn = False

        plain_ = []
        core_ = []
        inline_ = []
        no_commands_ = []

        for mod in self.allmodules.modules:
            if not hasattr(mod, "commands"):
                logger.debug(f"Module {mod.__class__.__name__} is not inited yet")
                continue

            if mod.strings["name"] in self.get("hide", []) and not force:
                continue

            tmp = ""

            try:
                name = mod.strings["name"]
            except KeyError:
                name = getattr(mod, "name", "ERROR")

            inline = (
                hasattr(mod, "callback_handlers")
                and mod.callback_handlers
                or hasattr(mod, "inline_handlers")
                and mod.inline_handlers
            )

            if not inline:
                for cmd_ in mod.commands.values():
                    try:
                        inline = "await self.inline.form(" in inspect.getsource(
                            cmd_.__code__
                        )
                    except Exception:
                        pass

            core = mod.__origin__ == "<core>"

            if core:
                emoji = self.config["core_emoji"]
            elif inline:
                emoji = self.config["acbot_emoji"]
            else:
                emoji = self.config["plain_emoji"]

            if (
                not getattr(mod, "commands", None)
                and not getattr(mod, "inline_handlers", None)
                and not getattr(mod, "callback_handlers", None)
            ):
                no_commands_ += [
                    self.strings("mod_tmpl").format(self.config["empty_emoji"], name)
                ]
                continue

            tmp += self.strings("mod_tmpl").format(emoji, name)
            first = True

            commands = [
                name
                for name, func in mod.commands.items()
                if await self.allmodules.check_security(message, func) or force
            ]

            for cmd in commands:
                if first:
                    tmp += self.strings("first_cmd_tmpl").format(cmd)
                    first = False
                else:
                    tmp += self.strings("cmd_tmpl").format(cmd)

            icommands = [
                name
                for name, func in mod.inline_handlers.items()
                if await self.inline.check_inline_security(
                    func=func,
                    user=message.sender_id,
                )
                or force
            ]

            for cmd in icommands:
                if first:
                    tmp += self.strings("first_cmd_tmpl").format(f"š¹ {cmd}")
                    first = False
                else:
                    tmp += self.strings("cmd_tmpl").format(f"š¹ {cmd}")

            if commands or icommands:
                tmp += " ]"
                if core:
                    core_ += [tmp]
                elif inline:
                    inline_ += [tmp]
                else:
                    plain_ += [tmp]
            elif not shown_warn and (mod.commands or mod.inline_handlers):
                reply = (
                    "<i>You have permissions to execute only these"
                    f" commands</i>\n{reply}"
                )
                shown_warn = True

        plain_.sort(key=lambda x: x.split()[1])
        core_.sort(key=lambda x: x.split()[1])
        inline_.sort(key=lambda x: x.split()[1])
        no_commands_.sort(key=lambda x: x.split()[1])
        no_commands_ = "".join(no_commands_) if force else ""

        partial_load = (
            ""
            if self.lookup("Loader")._fully_loaded
            else f"\n\n{self.strings('partial_load')}"
        )

        await self.inline.form(
            text=f"{reply}\n{''.join(core_)}{''.join(plain_)}{''.join(inline_)}{no_commands_}{partial_load}\n\n<i>AuthorChe'sā fresh and cute Telegram bot </i>",
            reply_markup=[
                [
                    {
                        "text": "Author's Channels",
                        "callback": self.amore,
                    },
                ],
                [{"text": "š» Close", "action": "close"}],
            ],
            message=message,
        )

    async def amore(self, call: InlineCall) -> None:
        await call.edit(
            text=f"<b>š³ Need talk? Feel free to join our Author's chat's.</b>",
            reply_markup=[
                [
                    {
                        "text": "AuthorChe'sā",
                        "url": "https://t.me/AuthorChe",
                    },
                    {
                        "text": "#offtop",
                        "url": "https://t.me/cherkassy_offtop",
                     },
                ],
                [{"text": "ŠŠ°ŠŗŃŠøŃŠø Š¼ŠµŠ½Ń", "action": "close"}],
            ],
        )

    
