<!--
SPDX-FileCopyrightText: 2026 Vadym Yemelianov (AuthorChe / VadymYem), AuthorBot integration and maintenance
SPDX-License-Identifier: AGPL-3.0-only
Existing upstream copyright and license notices are retained; see NOTICE.md and LICENSE.
-->

# Локалізація AuthorBot · by AuthorChe

Пакети: `en`, `ua`, `ru`, `de`, `ja`. Сумісні коди `uk` → `ua`, `jp` → `ja`; мова Telegram на кшталт `de-DE` нормалізується до `de`.

AuthorBot використовує власні локалізовані тексти привітання, публічних сторінок і термінальної заставки в секції `$public_pages`. Макет спільний для всіх мов у `acbot/public_pages.py`. Публічні сторінки обирають мову відвідувача; налаштування власника залишаються незалежними. Збережені редакторами сторінки мають пріоритет над стандартними.

Основні німецькі, японські та російські переклади адаптовано з [Heroku](https://github.com/coddrago/Heroku), revision `87d855ff50a404484c84f8ca4237d5c27c137b45`, ліцензія AGPL-3.0. Автори основи: Dan Gazizullin і Codrago. Збережено лише сумісні ключі та форматні аргументи; користувацькі тексти й посилання адаптовано до AuthorBot. Неперекладені рядки залишаються англійськими. Авторські тексти, брендування та оформлення AuthorBot — AuthorChe.

Новий переклад має зберігати ключі, HTML-теги та форматні аргументи оригіналу. Перевірки `scripts/selfcheck.py` і `scripts/runtimecheck.py` перевіряють завантаження пакетів, шаблони, мови та fallback.
