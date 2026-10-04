# SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem)
# SPDX-License-Identifier: AGPL-3.0-only

"""Owner-only lifecycle controls for native Termux and its PRoot guest."""

import os

from .. import loader, main, utils


def is_termux_runtime(environ=None):
    env = os.environ if environ is None else environ
    # Debian in PRoot reports Linux, so uname/OSTYPE alone is insufficient.
    return (env.get("AUTHORBOT_TERMUX") == "1"
            or "com.termux" in env.get("PREFIX", "")
            or "com.termux" in env.get("TERMUX__PREFIX", ""))


@loader.tds
class TermuxControlMod(loader.Module):
    """Коректна зупинка AuthorBot на Android у Termux або Debian/PRoot."""

    strings = {
        "name": "TermuxControl",
        "unsupported": "⚙️ <b>This command is available only in Termux on Android.</b>",
        "stopping": "🌙 <b>Stopping AuthorBot.</b>\nYour data will be saved. Run <code>authorbot</code> in Termux to start again.",
    }

    @loader.command()
    @loader.owner
    async def stop_acbot(self, message):
        """— save data and stop this AuthorBot process in Termux without restarting."""
        if not is_termux_runtime():
            await utils.answer(message, self.strings("unsupported"))
            return
        await utils.answer(message, self.strings("stopping"))
        main.acbot.request_stop()
