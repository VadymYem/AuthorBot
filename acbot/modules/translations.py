# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
# SPDX-License-Identifier: AGPL-3.0-only
# Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.

# ©️ Dan G. && AuthorChe
# AGPL-3.0 · https://www.gnu.org/licenses/agpl-3.0.html

import logging

from herokutl.tl.types import Message

from .. import loader, translations, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class Translations(loader.Module):
    """Processes internal translations"""

    strings = {"name": "Translations"}

    async def _change_language(self, call: InlineCall, lang: str):
        self._db.set(translations.__name__, "lang", lang)
        await self.allmodules.reload_translations()

        await call.edit(self.strings("lang_saved").format(self._get_flag(lang)))

    def _get_flag(self, lang: str) -> str:
        flags = {"en": "🇬🇧", "ua": "🇺🇦", "ru": "🇷🇺", "de": "🇩🇪", "ja": "🇯🇵"}
        return flags.get(translations.normalize_language(lang), "🌍")

    @loader.command()
    async def setlang(self, message: Message):
        if not (args := utils.get_args_raw(message)):
            await self.inline.form(
                message=message,
                text=self.strings("choose_language"),
                reply_markup=utils.chunks(
                    [
                        {
                            "text": text,
                            "callback": self._change_language,
                            "args": (lang,),
                        }
                        for lang, text in translations.SUPPORTED_LANGUAGES.items()
                    ],
                    2,
                ),
            )
            return

        if any(len(i) != 2 and not utils.check_url(i) for i in args.split()):
            await utils.answer(message, self.strings("incorrect_language"))
            return

        args = " ".join(token if utils.check_url(token) else translations.normalize_language(token) for token in args.split())

        seen = set()
        seen_add = seen.add
        args = " ".join(x for x in args.split() if not (x in seen or seen_add(x)))

        self._db.set(translations.__name__, "lang", args)
        await self.allmodules.reload_translations()

        await utils.answer(
            message,
            self.strings("lang_saved").format(
                "".join(
                    [
                        (
                            self._get_flag(lang)
                            if not utils.check_url(lang)
                            else "📁"
                        )
                        for lang in args.split()
                    ]
                )
            )
            + (
                ("\n\n" + self.strings("not_official"))
                if any(
                    lang not in translations.SUPPORTED_LANGUAGES
                    for lang in args.split()
                )
                else ""
            ),
        )

    @loader.command()
    async def dllangpackcmd(self, message: Message):
        if not (args := utils.get_args_raw(message)) or not utils.check_url(args):
            await utils.answer(message, self.strings("check_url"))
            return

        current_lang = (
            " ".join(
                lang
                for lang in self._db.get(translations.__name__, "lang", None).split()
                if not utils.check_url(lang)
            )
            if self._db.get(translations.__name__, "lang", None)
            else None
        )

        self._db.set(
            translations.__name__,
            "lang",
            f"{current_lang} {args}" if current_lang else args,
        )

        await utils.answer(
            message,
            self.strings(
                "pack_saved"
                if await self.allmodules.reload_translations()
                else "check_pack"
            ),
        )
