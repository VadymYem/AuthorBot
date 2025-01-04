# © Dan G. && AuthorChe
#  
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
#  https://www.gnu.org/licenses/agpl-3.0.html
# -*- coding: utf-8 -*-

import logging

from hikkatl.tl.types import Message

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
        emoji_flags = {
            "ðŸ‡¬ðŸ‡§": "<emoji document_id=6323589145717376403>ðŸ‡¬ðŸ‡§</emoji>",
            "ðŸ‡ºðŸ‡¿": "<emoji document_id=6323430017179059570>ðŸ‡ºðŸ‡¿</emoji>",
            "ðŸ‡·ðŸ‡º": "<emoji document_id=6323139226418284334>ðŸ¤®</emoji>",
            "ðŸ‡ºðŸ‡¦": "<emoji document_id=5276140694891666474>ðŸ‡ºðŸ‡¦</emoji>",
            "ðŸ‡®ðŸ‡¹": "<emoji document_id=6323471399188957082>ðŸ‡®ðŸ‡¹</emoji>",
            "ðŸ‡©ðŸ‡ª": "<emoji document_id=6320817337033295141>ðŸ‡©ðŸ‡ª</emoji>",
            "ðŸ‡ªðŸ‡¸": "<emoji document_id=6323315062379382237>ðŸ‡ªðŸ‡¸</emoji>",
            "ðŸ‡¹ðŸ‡·": "<emoji document_id=6321003171678259486>ðŸ‡¹ðŸ‡·</emoji>",
            "ðŸ‡°ðŸ‡¿": "<emoji document_id=6323135275048371614>ðŸ‡°ðŸ‡¿</emoji>",
            "ðŸ¥Ÿ": "<emoji document_id=5382337996123020810>ðŸ¥Ÿ</emoji>",
        }

        lang2country = {"en": "ðŸ‡¬ðŸ‡§", "tt": "ðŸ¥Ÿ", "kk": "ðŸ‡°ðŸ‡¿", "ua": "ðŸ‡ºðŸ‡¦", "ru":"ðŸ¤®"}

        lang = lang2country.get(lang) or utils.get_lang_flag(lang)
        return emoji_flags.get(lang, lang)

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
                            else "<emoji document_id=5433653135799228968>ðŸ“</emoji>"
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
