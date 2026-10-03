<div align="center">

<img src="assets/authorbot_banner.svg" width="100%" alt="AuthorBot — by Author C">

# AuthorBot

### Telegram userbot, built around modules, automation and modern Telegram UI

[![Python](https://img.shields.io/badge/Server_Python-3.10–3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-MTProto%20%2B%20Bot%20API-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/)
[![License](https://img.shields.io/badge/License-AGPLv3-663399)](LICENSE)
[![Rich Messages](https://img.shields.io/badge/Rich%20Messages-Bot%20API%2010.x-111827)](https://core.telegram.org/bots/api#rich-messages)
[![Verify](https://github.com/VadymYem/AuthorBot/actions/workflows/verify.yml/badge.svg)](https://github.com/VadymYem/AuthorBot/actions/workflows/verify.yml)

**AuthorBot** — модульний Telegram userbot від **Author C**.  
Працює як розширення вашого Telegram-акаунта та окремий inline/public bot-інтерфейс.

[Website](https://authorche.top) · [Installation](https://authorche.top/ubot.html) · [Telegram](https://t.me/wsinfo) · [Module guide](docs/MODULE_DEVELOPMENT.md)

</div>

---

## Що вміє AuthorBot

| Напрям | Можливості |
|---|---|
| **Модулі** | Динамічне встановлення, оновлення, локальний cache, dependency install, aliases |
| **Inline UI** | Форми, списки, галереї, callback-кнопки, inline queries |
| **Rich Messages** | Rich HTML/Markdown, headings, tables, details, media blocks, rich buttons, streaming drafts |
| **Безпека** | Owner/security masks, targeted rules, blacklist, API flood protection, без прихованого owner-доступу |
| **Дані** | Локальна JSON DB з атомарним записом і backup; optional Redis із fallback на диск |
| **Оновлення** | Fetch + deterministic reset до upstream branch без merge-conflict loop |
| **Backup** | Backup/restore конфігурації та модулів |
| **Termux** | Ізольоване Python virtualenv, autostart, кольоровий banner |
| **Public bot** | `/start`, `/help`, `/about`, `/projects` із Rich Message оформленням |

### Основний каталог модулів

AuthorBot використовує як primary repository:

```text
https://github.com/hikariatama/host/raw/master
```

Додаткові repositories можна налаштовувати через конфіг Loader.

---

## Android / Termux

> Рекомендовано актуальний Termux із F-Droid або GitHub releases.

```bash
termux-wake-lock
pkg update -y
pkg install -y wget git python openssl
clear
bash -c "$(wget -qO- https://raw.githubusercontent.com/VadymYem/AuthorBot/main/termux.sh)"
```

Інсталятор:

- встановлює системні залежності;
- клонує чистий upstream;
- створює `.venv`;
- встановлює Python requirements без забруднення глобального Python;
- конфігурує Termux autostart;
- запускає `python -m acbot`.

Після встановлення:

```bash
cd ~/AuthorBot
./.venv/bin/python -m acbot
```

---

## Linux / VPS

Production-профіль для Linux/VPS тестується на **Python 3.10 та 3.11**. Для чистої установки:

```bash
git clone https://github.com/VadymYem/AuthorBot.git
cd AuthorBot
bash install.sh
```

### Docker

```bash
bash docker.sh
```

Docker за замовчуванням публікує web UI тільки на `127.0.0.1:8085` і генерує окремий випадковий пароль у приватному `.env`. Для свідомого зовнішнього bind встановіть `BIND_ADDRESS=0.0.0.0` та використовуйте сильний `AUTHORBOT_WEB_PASSWORD`.

---

## Public companion bot

Під час налаштування inline-режиму AuthorBot створює або використовує BotFather-бота. Для автоматично створеного бота використовується ім’я **Author Bot off** і випадковий username формату:

```text
author_<random>_off_AC_bot
```

Публічно доступні команди:

- `/start` — головна Rich Message сторінка;
- `/help` — довідка;
- `/about` — інформація про Author C;
- `/projects` — проєкти та офіційні ресурси.

Редактори з дозволеними Telegram ID можуть оновлювати ці сторінки командами `/setstart`, `/sethelp`, `/setabout`, `/setprojects`. Контент зберігається локально в DB конкретного встановлення.

---

## Telegram Rich Messages

AuthorBot має окремий transport для сучасних Rich Message методів Bot API, тому підтримка `sendRichMessage` і `sendRichMessageDraft` не залежить від можливостей старого inline framework:

```python
await self.inline.rich.send(
    self._client.tg_id,
    html="<h1>Hello from AuthorBot</h1><p>Native Rich Message.</p>",
)
```

Підтримуються:

- Rich HTML і Rich Markdown;
- explicit blocks;
- media references;
- `sendRichMessage`;
- `sendRichMessageDraft`;
- нові rich buttons;
- direct raw Bot API methods через `self.inline.rich.request(...)`.

Для тесту після запуску:

```text
.richdemo
```

Повний приклад модуля: [docs/MODULE_DEVELOPMENT.md](docs/MODULE_DEVELOPMENT.md).

---

## Архітектура

```text
acbot/
├── inline/             Bot API, forms, galleries, Rich Messages
├── modules/            core modules
├── langpacks/          translations
├── web/                local web authorization/config UI
├── database.py         local + optional Redis persistence
├── dispatcher.py       command/watchers dispatch
├── loader.py           module registration and lifecycle
├── security.py         permission model
└── main.py             Telegram client lifecycle
```

External modules завантажуються окремо та не повинні змінювати core-файли.

---

## Безпека

AuthorBot не повинен:

- логувати BotFather token, API hash, session auth key або паролі;
- автоматично додавати сторонні Telegram ID до owner-групи;
- передавати локальну DB сторонньому сервісу без явної конфігурації;
- виконувати remote code поза свідомо встановленими Python-модулями.

Сесії, DB та локальні налаштування не комітяться в Git. Для Redis діє fallback на локальний атомарний snapshot.

Докладніше: [SECURITY.md](SECURITY.md).

---

## Розробка модулів

Документація містить:

- структуру модуля;
- commands / watchers / inline handlers / callbacks;
- DB і config;
- security;
- Rich Messages;
- правила dependency loading;
- стабільне очищення ресурсів у `on_unload`.

→ **[Module Development Guide](docs/MODULE_DEVELOPMENT.md)**

---

## Автор

**Author C**

- Website: https://authorche.top
- Telegram: https://t.me/wsinfo
- AuthorGram: https://t.me/authorgram_apk
- Google Play: https://play.google.com/store/apps/details?id=toss.authorgram.apk

---

## License

GNU Affero General Public License v3.0. Див. [LICENSE](LICENSE).
