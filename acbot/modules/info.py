# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

__version__ = (2, 5, 0)

#              © Copyright 2022
#
# https://t.me/AuthorChe
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta developer: @AuthorChe

# scope: inline
# scope: acbot_only
# scope: acbot_min 1.1.27

import logging
import git

from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, main, translations, utils
from ..public_pages import heading, text as page_text
from ..branding import DEFAULT_BANNER, LEGACY_BANNERS
import datetime
from ..inline.types import InlineQuery

logger = logging.getLogger(__name__)


@loader.tds
class acbotInfoMod(loader.Module):
    """Show 𝙰𝚞𝚝𝚑𝚘𝚛𝙲𝚑𝚎'𝚜 info"""

    strings = {
        "name": "Info",
        "owner": "Owner",
        "version": "Version",
        "build": "Build",
        "prefix": "Prefix",
        "_cfg_time": "Time zone offset from UTC, in hours.",
        "_cfg_close": "Label of the Close button.",
        "send_info": "Показати інформацію про бота.",
        "description": "ℹ This will not compromise any sensitive info.",
        "up-to-date": "😌 Up-to-date.",
        "update_required": "😕 Update required </b><code>.update</code><b>",
        "_cfg_cst_msg": "Custom message for info. May contain {me}, {version}, {build}, {prefix}, {platform}, {upd} keywords.",
        "_cfg_cst_btn": "Custom button. Leave empty to remove button.",
        "_cfg_cst_bnr": "Custom Banner.",
        "_cfg_cst_frmt": "Custom fileformat for Banner.",
        "_cfg_banner": "Set `True` in order to disable an media banner.",
        "_cfg_inline_banner": "Set `True` in order to disable an inline media banner.",
    }

    strings_ua = {
        "owner": "Власник",
        "version": "Версія",
        "build": "Збірка",
        "prefix": "Префікс",
        "_cfg_time": "Зсув часового поясу від UTC у годинах.",
        "_cfg_close": "Текст кнопки закриття.",
        "send_info": "Показати інформацію про бота.",
        "description": "ℹ Це не розкриє особистої інформації :)",
        "_ihandle_doc_info": "Показати інформацію про бота.",
        "up-to-date": "😌 Актуальна версія.",
        "update_required": "😕 Потрібне оновлення </b><code>.update</code><b>",
        "_cfg_cst_msg": "Власний текст повідомлення в info. Може мати ключові слова {me}, {version}, {build}, {prefix}, {platform}, {upd}.",
        "_cfg_cst_btn": "Власна кнопка в info. Залиште порожньою, щоб прибрати.",
        "_cfg_cst_bnr": "Власний банер.",
        "_cfg_cst_frmt": "Формат файлу банера.",
        "_cfg_banner": "Постав `True`, щоб вимкнути банер-картинку.",
        "_cfg_inline_banner": "Встановіть `True`, щоб вимкнути inline медіа-банер",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                "no",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "custom_banner",
                DEFAULT_BANNER,
                lambda: self.strings("_cfg_cst_bnr"),
            ),
            loader.ConfigValue(
                "custom_format",
                "photo",
                lambda: self.strings("_cfg_cst_frmt"),
                validator=loader.validators.Choice(["photo", "video", "audio", "gif"]),
            ),
            loader.ConfigValue(
                "disable_banner",
                False,
                lambda: self.strings("_cfg_banner"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "disable_inline_banner",
                False,
                lambda: self.strings("_cfg_inline_banner"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "timezone",
                3,
                lambda: self.strings("_cfg_time"),
                validator=loader.validators.Integer(minimum=-12, maximum=14),
            ),
            loader.ConfigValue(
                "close_btn",
                "🔻Close",
                lambda: self.strings("_cfg_close"),
            ),
            loader.ConfigValue(
                "custom_button1",
                ["🌐WebSite", "https://authorche.top/ubot"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button2",
                ["Donate❤️", "https://authorche.top/donate"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button3",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button4",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button5",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button6",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button7",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button8",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button9",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button10",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button11",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
            loader.ConfigValue(
                "custom_button12",
                [],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(min_len=0, max_len=2),
            ),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me()

    def _snapshot(self):
        esc = utils.escape_html
        ver = utils.get_git_hash() or "Unknown"
        try:
            diff = git.Repo().git.log(["HEAD..origin/main", "--oneline"])
            upd = (self.strings("update_required") if diff else self.strings("up-to-date")).replace('</b>', '').replace('<b>', '')
        except Exception:
            upd = ""
        try:
            offset = datetime.timedelta(hours=int(self.config["timezone"]))
            clock = datetime.datetime.now(datetime.timezone(offset)).strftime("%H:%M:%S")
        except (TypeError, ValueError):
            clock = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        return {
            "me": f'<a href="tg://user?id={self._me.id}">{esc(get_display_name(self._me))}</a>',
            "version": esc(".".join(map(str, main.__version__))),
            "build": f'<a href="https://github.com/VadymYem/AuthorBot/commit/{ver}">#{ver[:8]}</a>',
            "prefix": f'<code>{esc(self.get_prefix())}</code>',
            "platform": utils.get_named_platform(),
            "uptime": esc(utils.formatted_uptime()), "time": clock, "upd": upd,
        }

    def _render_info(self, values=None) -> str:
        values = values or self._snapshot()
        if self.config["custom_message"] != "no":
            return self.config["custom_message"].format(**values)
        return ("<b>AuthorBot</b>\n"
                + "\n".join(f'<b>{self.strings(key)}:</b> {values[field]}'
                            for key, field in (("owner", "me"), ("version", "version"),
                                               ("build", "build"), ("prefix", "prefix")))
                + f'\n{values["upd"]}\n⏳ {values["uptime"]} · ⌚ {values["time"]}\n{values["platform"]}')

    def _render_rich_info(self, values=None):
        values = values or self._snapshot()
        language = self._db.get(translations.__name__, "lang", "en").split()[0]
        content = [heading("AuthorBot · " + page_text("info_title", language), "by AuthorChe"), '<hr/>']
        if self.config["custom_message"] != "no":
            content.append('<section>' + self._render_info(values).replace('\n', '<br/>') + '</section>')
        else:
            fields = [(self.strings(key), values[field]) for key, field in
                      (("owner", "me"), ("version", "version"), ("build", "build"), ("prefix", "prefix"))]
            fields += [(page_text(label, language), values[field]) for label, field in
                       (("uptime", "uptime"), ("time_label", "time"), ("platform_label", "platform"))]
            content.append('<table bordered striped compact>' + ''.join(
                f'<tr><td><b>{utils.escape_html(label)}</b></td><td>{value}</td></tr>'
                for label, value in fields) + '</table>')
            if values["upd"]:
                # Legacy status strings had closing/opening bold tags intended
                # for the classic template. Balance them before rich rendering.
                status = values["upd"].replace('</b>', '').replace('<b>', '')
                content.append('<blockquote>' + status + '</blockquote>')
        content += ['<footer>© 2026 AuthorChe · AuthorBot · AGPLv3</footer>']
        return '\n'.join(content)

    def _get_mark(self, btn_count):
        btn_count = str(btn_count)
        button = self.config[f"custom_button{btn_count}"]
        return (
            {
                "text": self.config[f"custom_button{btn_count}"][0],
                "url": self.config[f"custom_button{btn_count}"][1],
            }
            if len(button) == 2 and utils.check_url(button[1])
            else None
        )

    def _buttons(self, close=False):
        buttons = [button for i in range(1, 13) if (button := self._get_mark(i))]
        rows = list(utils.chunks(buttons, 3))
        if close:
            rows += [[{"text": self.config["close_btn"], "action": "close"}]]
        return rows

    async def _rich_payload(self, values, inline=False):
        html = self._render_rich_info(values)
        banner = await self._banner(inline=inline)
        media = []
        if banner:
            kind, source = next(iter(banner.items()))
            kind = "animation" if kind == "gif" else kind
            tag = "img" if kind == "photo" else "audio" if kind == "audio" else "video"
            html = html.replace('<hr/>', f'<hr/><figure><{tag} src="tg://{kind}?id=info_banner"/></figure>', 1)
            media = [{"id": "info_banner", "media": {"type": kind, "media": source}}]
        return html, media, banner

    @loader.inline_everyone
    async def info_inline_handler(self, query: InlineQuery) -> dict:
        """Подивитися інформацію про бота."""
        values = self._snapshot()
        html, media, banner = await self._rich_payload(values, inline=True)
        return {
            "title": self.strings("send_info"), "description": self.strings("description"),
            ("caption" if banner else "message"): self._render_info(values), **banner,
            "rich_html": html, "rich_media": media,
            "reply_markup": self._buttons(),
        }

    @loader.unrestricted
    async def infocmd(self, message: Message):
        """Send bot info as an interactive Rich Message."""
        values = self._snapshot()
        html, media, banner = await self._rich_payload(values)
        await self.inline.form(
            message=message, text=self._render_info(values), rich_html=html, rich_media=media,
            reply_markup=self._buttons(close=True), ttl=15 * 60,
            **banner,
        )

    async def _banner(self, inline: bool = False) -> dict:
        if self.config["disable_inline_banner" if inline else "disable_banner"]:
            return {}
        banner = self.config["custom_banner"]
        if banner == DEFAULT_BANNER or banner in LEGACY_BANNERS:
            return {"photo": await self.inline.brand_photo()}
        return {self.config["custom_format"]: banner} if banner else {}
