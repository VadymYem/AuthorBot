
#            © Copyright 2022
#
#          https://t.me/vadym_yem
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta developer: @authorche
import logging
import time

from telethon.tl.types import Message

from .. import loader
from ..inline.types import InlineCall, InlineQuery

logger = logging.getLogger(__name__)


@loader.tds
class PingerMod(loader.Module):
    """Inline Pinger For Test"""

    strings = {
        "name": "InlinePing",
        "results_ping": "⏱️ <b>𝙰𝚞𝚝𝚑𝚘𝚛𝙲𝚑𝚎'𝚜✍ ping:</b> <code>{}</code> <b>ms</b>"
    }

    @loader.command(ru_doc="Check 𝙰𝚞𝚝𝚑𝚘𝚛𝙲𝚑𝚎'𝚜✍ ping")
    async def iping(self, message: Message):
        """Test AuthorChe's ping"""
        start = time.perf_counter_ns()

        await self.inline.form(
            self.strings("results_ping").format(
                round((time.perf_counter_ns() - start) / 10**3, 3),
            ),
            reply_markup=[[{"text": "⏱ Now ", "callback": self.nowping}]],
            message=message,
        )

    async def nowping(self, call: InlineCall):
        start = time.perf_counter_ns()
        await call.edit(
			self.strings("results_ping").format(
                round((time.perf_counter_ns() - start) / 10**3, 3),
            ),
			reply_markup=[[{"text": "⏱ Now", "callback": self.nowping,}],]
		)

    async def ping_inline_handler(self, query: InlineQuery):
        """Test AuthorChe's ping"""
        start = time.perf_counter_ns()
        ping = self.strings("results_ping").format(
                round((time.perf_counter_ns() - start) / 10**3, 3),
            )
        button = [{
                    "text": "⏱ Now", 
                    "callback": self.nowping
                 }]
        return {
            "title": "Ping",
            "description": "Tap here",
            "thumb": "https://ralphmaltby.com/wp-content/uploads/2015/06/Ping-Logo.jpg",
            "message": ping,
            "reply_markup": button,
        }
