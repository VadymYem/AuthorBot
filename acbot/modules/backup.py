
#              © Copyright 2022
#           https://t.me/authorche
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import datetime
import io
import json
import logging
import time

from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import BotInlineCall

logger = logging.getLogger(__name__)


@loader.tds
class AcbotBackupMod(loader.Module):
    """Automatic database backup"""

    strings = {
        "name": "Backup",
        "period": (
            "⌚️ <b>Unit «ALPHA»</b> creates database backups periodically. You can"
            " change this behavior later.\n\nPlease, select the periodicity of"
            " automatic database backups"
        ),
        "saved": (
            "✅ Backup period saved. You can re-configure it later with"
            " .set_backup_period"
        ),
        "never": (
            "✅ I will not make automatic backups. You can re-configure it later with"
            " .set_backup_period"
        ),
        "invalid_args": (
            "🚫 <b>Specify correct backup period in hours, or `0` to disable</b>"
        ),
    }

    strings_ua = {
        "period": (
            "⌚️ <b>Привіт. Я юнiт «Backuper»</b> створюю регулярні резервні копії. Ці налаштування"
            " можна змінити пізніше.\n\Будь-ласка, виберіть період резервного"
            " копіювання"
        ),
        "saved": (
            "✅ Період збережено! Його можна змінити використавши .set_backup_period"
        ),
        "never": (
            "✅ Я не буду робити автоматично резервні копії. Можна відмінити"
            " використавши .set_backup_period"
        ),
        "invalid_args": (
            "🚫 <b>Вкажи правильний період в годинах, або `0` для вимкнення</b>"
        ),
    }

    async def client_ready(self):
        if not self.get("period"):
            await self.inline.bot.send_photo(
                self.tg_id,
                photo="https://images.app.goo.gl/hmFg6gnowBfLsMWA8",
                caption=self.strings("period"),
                reply_markup=self.inline.generate_markup(
                    utils.chunks(
                        [
                            {
                                "text": f"🕰 {i} h",
                                "callback": self._set_backup_period,
                                "args": (i,),
                            }
                            for i in {1, 2, 4, 6, 8, 12, 24, 48, 168}
                        ],
                        3,
                    )
                    + [
                        [
                            {
                                "text": "🚫 Never",
                                "callback": self._set_backup_period,
                                "args": (0,),
                            }
                        ]
                    ]
                ),
            )

        self._backup_channel, _ = await utils.asset_channel(
            self._client,
            "backups",
            "📼 Your database backups will appear there",
            silent=True,
            archive=True,
            avatar="https://notagrouch.com/wp-content/uploads/2013/06/data-backup-wordpress.jpg",
            _folder="acbot",
        )

        self.handler.start()

    async def _set_backup_period(self, call: BotInlineCall, value: int):
        if not value:
            self.set("period", "disabled")
            await call.answer(self.strings("never"), show_alert=True)
            await call.delete()
            return

        self.set("period", value * 60 * 60)
        self.set("last_backup", round(time.time()))

        await call.answer(self.strings("saved"), show_alert=True)
        await call.delete()

    @loader.command(ua_doc="<час в годинах> - Встановити частоту резервного копіювання")
    async def set_backup_period(self, message: Message):
        """<time in hours> - Change backup frequency"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit() or int(args) not in range(200):
            await utils.answer(message, self.strings("invalid_args"))
            return

        if not int(args):
            self.set("period", "disabled")
            await utils.answer(message, f"<b>{self.strings('never')}</b>")
            return

        period = int(args) * 60 * 60
        self.set("period", period)
        self.set("last_backup", round(time.time()))
        await utils.answer(message, f"<b>{self.strings('saved')}</b>")

    @loader.loop(interval=1)
    async def handler(self):
        try:
            if not self.get("period"):
                await asyncio.sleep(3)
                return

            if not self.get("last_backup"):
                self.set("last_backup", round(time.time()))
                await asyncio.sleep(self.get("period"))
                return

            if self.get("period") == "disabled":
                raise loader.StopLoop

            await asyncio.sleep(
                self.get("last_backup") + self.get("period") - time.time()
            )

            backup = io.BytesIO(json.dumps(self._db).encode("utf-8"))
            backup.name = "acbot-db-backup-{}.json".format(
                getattr(datetime, "datetime", datetime).now().strftime("%d-%m-%Y-%H-%M")
            )

            await self._client.send_file(self._backup_channel, backup)
            self.set("last_backup", round(time.time()))
        except loader.StopLoop:
            raise
        except Exception:
            logger.exception("acbotBackup failed")
            await asyncio.sleep(60)
