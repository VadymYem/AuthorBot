# ©️ Dan G. && AuthorChe
# 🌐 
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html
import re
import string
import sys
import typing


def tty_print(text: str, tty: bool):
    """
    Print text to terminal if tty is True,
    otherwise removes all ANSI escape sequences
    """
    print(text if tty else re.sub(r"\033\[[0-9;]*m", "", text))


def tty_input(text: str, tty: bool) -> str:
    """
    Print text to terminal if tty is True,
    otherwise removes all ANSI escape sequences
    """
    try:
        return input(text if tty else re.sub(r"\033\[[0-9;]*m", "", text))
    except EOFError:
        tty_print("\nВвід у терміналі закрито. Запусти authorbot, щоб продовжити вхід.", tty)
        raise SystemExit(2) from None


def api_config(tty: typing.Optional[bool] = None):
    """Request API config from user and set"""
    from . import main

    if tty is None:
        tty = sys.stdout.isatty()

    tty_print("\033[1;35mAuthorBot by AuthorChe · Вхід у Telegram\033[0m", tty)
    tty_print("\033[0;96m1. Відкрий https://my.telegram.org та увійди.\033[0m", tty)
    tty_print("\033[0;96m2. Обери \033[1;96mAPI development tools\033[0m", tty)
    tty_print(
        (
            "\033[0;96m3. Створи застосунок, заповнивши його дані.\033[0m"
        ),
        tty,
    )
    tty_print(
        (
            "\033[0;96m4. Скопіюй \033[1;96mAPI ID\033[0;96m та \033[1;96mAPI"
            " hash\033[0m"
        ),
        tty,
    )

    while api_id := tty_input("\033[0;95mВведи API ID: \033[0m", tty):
        if api_id.isdigit():
            break

        tty_print("\033[0;91mAPI ID має містити лише цифри.\033[0m", tty)

    if not api_id:
        tty_print("\033[0;91mВхід скасовано.\033[0m", tty)
        sys.exit(0)

    while api_hash := tty_input("\033[0;95mВведи API hash: \033[0m", tty):
        if len(api_hash) == 32 and all(
            symbol in string.hexdigits for symbol in api_hash
        ):
            break

        tty_print("\033[0;91mAPI hash має містити 32 шістнадцяткові символи.\033[0m", tty)

    if not api_hash:
        tty_print("\033[0;91mВхід скасовано.\033[0m", tty)
        sys.exit(0)

    main.save_config_key("api_id", int(api_id))
    main.save_config_key("api_hash", api_hash)
    tty_print("\033[0;92mДані API збережено.\033[0m", tty)
