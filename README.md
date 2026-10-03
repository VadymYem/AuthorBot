<div align="center">

<img src="assets/authorbot_banner.svg" width="100%" alt="AuthorBot — by Author C">

# AuthorBot

### Telegram userbot, built around modules, automation and modern Telegram UI

[![Python](https://img.shields.io/badge/Server_Python-3.10–3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-MTProto%20%2B%20Bot%20API-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/)
[![License](https://img.shields.io/badge/License-AGPLv3-663399)](LICENSE)
[![Rich Messages](https://img.shields.io/badge/Rich%20Messages-Bot%20API%2010.x-111827)](https://core.telegram.org/bots/api#rich-messages)
[![Verify](https://github.com/AuthorGramProject/AuthorBot/actions/workflows/verify.yml/badge.svg)](https://github.com/AuthorGramProject/AuthorBot/actions/workflows/verify.yml)

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
| **Termux** | Debian Bookworm / Python 3.11 через PRoot, virtualenv, autostart |
| **Public bot** | `/start`, `/help`, `/about`, `/projects` із Rich Message оформленням |

### Основний каталог модулів

AuthorBot використовує як primary repository:

```text
https://github.com/hikariatama/host/raw/master
```

Додаткові repositories можна налаштовувати через конфіг Loader.

---

## Android / Termux

> Потрібен Termux із F-Droid або GitHub releases. Для приватного репозиторію використовуйте налаштовану Git-автентифікацію. Інсталятор використовує Debian Bookworm із Python 3.11 через PRoot-Distro 5+, без root. Системний Python Termux 3.13 не використовується для бота. На перше встановлення потрібні додатковий час і вільне місце для Debian та бібліотек.

```bash
(
  set -e
  termux-wake-lock
  pkg update -y
  pkg install -y curl
  installer="$(mktemp "$PREFIX/tmp/authorbot-bootstrap.XXXXXX")"
  trap 'rm -f "$installer"' EXIT
  curl -fL --retry 3 https://raw.githubusercontent.com/AuthorGramProject/AuthorBot/main/bootstrap-termux.sh -o "$installer"
  bash "$installer"
)
```

Вставте блок після появи запрошення `~ $` і дочекайтеся завершення. Він автоматично встановлює Git і PRoot-Distro, клонує або оновлює `~/AuthorBot`, готує Debian із Python 3.11, установлює всі бібліотеки, перевіряє їх та запускає бот. Під час першого входу потрібно ввести дані Telegram. Root і ручне налаштування Debian не потрібні.

Цей спосіб завантаження призначений для публічного репозиторію. Для приватної копії спочатку клонуйте її через власну Git-автентифікацію, потім виконайте `bash ~/AuthorBot/termux.sh`.

Інсталятор:

- встановлює окреме середовище Debian Bookworm;
- використовує вже завантажений репозиторій;
- створює `.venv-proot` із Python 3.11;
- встановлює основні й додаткові requirements та зупиняється у разі помилки;
- перевіряє залежності та виконує тести запуску перед стартом;
- конфігурує Termux autostart;
- запускає `python -m acbot`.

Після встановлення:

```bash
authorbot
```

Для оновлення спочатку зупиніть бот, потім:

```bash
git -C ~/AuthorBot pull --ff-only
bash ~/AuthorBot/termux.sh
```

Сесії та база даних залишаються у `~/AuthorBot`; інсталятор не скидає локальні зміни Git. Вивід встановлення видно в терміналі та записано в `~/authorbot-install.log`. `NO_AUTOSTART=1` вимикає додавання автозапуску до профілю, `AUTHORBOT_INSTALL_ONLY=1` завершує встановлення без запуску бота.

---

## Linux / VPS

Production-профіль для Linux/VPS тестується на **Python 3.10 та 3.11**. Для чистої установки:

```bash
git clone https://github.com/AuthorGramProject/AuthorBot.git
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

## Перевірки

```bash
python -m pip check
python scripts/selfcheck.py
python scripts/runtimecheck.py
```

CI перевіряє Python 3.10 і 3.11 з основними та додатковими залежностями, імпорти всіх основних і вбудованих модулів, регресійні сценарії та Docker-образ. Зображення в Telegram завантажуються з файлів репозиторію; вебінтерфейс віддає їх локально, незалежно від доступності приватного GitHub.

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
