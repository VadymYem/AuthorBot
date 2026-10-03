<div align="center">
  <img src="https://authorche.top/poems/logo.jpg" alt="AuthorBot Logo" width="200" style="border-radius: 50%;">
  
  # 🚀 AuthorBot v2.1
  
  <p>
    <b>The Ultimate Branded Telegram Userbot</b><br>
    <i>Fast, Secure, and Architecturally Perfected.</i>
  </p>

  <p>
    <a href="https://github.com/VadymYem/AuthorBot/stargazers"><img src="https://img.shields.io/github/stars/VadymYem/AuthorBot?color=28a0dc&style=for-the-badge&logo=github" alt="Stars"></a>
    <a href="https://github.com/VadymYem/AuthorBot/network/members"><img src="https://img.shields.io/github/forks/VadymYem/AuthorBot?color=18cc18&style=for-the-badge&logo=github" alt="Forks"></a>
    <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Telegram-MTProto-blue?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram">
  </p>

  <p>
    <a href="https://authorche.top">🌐 Website</a> •
    <a href="https://authorche.top/ubot.html">📖 Installation Guide</a> •
    <a href="https://authorche.top/donate.html">💌 Donate</a>
  </p>
</div>

---

## ✨ Основні переваги (Features)

AuthorBot — це вершина еволюції юзерботів, створена на базі стабільних оновлень та новітнього Telegram API.

*   🇺🇦 **Повна підтримка української мови:** Нативний переклад всіх інтерфейсів.
*   ⚡️ **HerokuTL 2.1.0:** Надшвидке ядро з повною підтримкою реакцій, відео-стікерів та кастомних емодзі.
*   🔒 **Висока безпека:** Інтегроване нативне кешування, оптимізація бази даних та захист сесій.
*   🎨 **Красивий UI/UX & Веб-Логін:** Брендований інтерфейс авторизації безпосередньо у вашому браузері.
*   🤖 **AI-Екосистема:** Вбудовані розумні модулі, які використовують Gemini та Groq.
*   👨‍👦 **NoNick (Мульти-аккаунт):** Дозволяє підключати окремі акаунти під юзербот, зберігаючи основний акаунт чистим.

---

## 📱 Встановлення на Android (Termux)

> [!IMPORTANT]
> Використовуйте Termux **тільки з F-Droid**, версія з Play Store є застарілою! [Завантажити APK тут](https://f-droid.org/repo/com.termux_118.apk).

**1.** Отримайте **API ID** та **API HASH** на [my.telegram.org](https://my.telegram.org).  
**2.** Відкрийте Termux та виконайте цю команду:

```bash
termux-wake-lock && pkg upgr -y && pkg i wget ncurses-utils python openssl git -y && clear && . <(wget -qO- https://raw.githubusercontent.com/VadymYem/AuthorBot/refs/heads/main/termux.sh)
```
**3.** Дотримуйтесь інструкцій на екрані та пройдіть авторизацію за допомогою веб-інтерфейсу або через термінал.

---

## 💻 Встановлення на Ubuntu / Debian / VPS

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install git python3 python3-pip -y
git clone https://github.com/VadymYem/AuthorBot
cd AuthorBot
pip install -r requirements.txt
pip install -r optional_requirements.txt  # опціональні пакети
python3 -m acbot --proxy-pass
```
*`--proxy-pass` необхідний для доступу до веб-панелі авторизації, якщо ви запускаєте бота на віддаленому сервері (VPS).*

---

## 🔧 Корисні аргументи запуску

| Аргумент | Опис |
|----------|------|
| `--proxy-pass` | Відкриває веб-панель для авторизації на VPS |
| `--root` | Дозволяє запуск від root-користувача |
| `--wipe` або `-w` | Повне видалення сесій, баз даних та модулів |
| `--data-root <path>` | Вказує кастомну директорію для даних |

---

## 🧠 Авторські ШІ Модулі

AuthorBot містить ексклюзивні розумні модулі. Для їх активації введіть ці команди в `Збережене` (Saved Messages):

```text
.dlmod downloads/ai_mods/AIContext.py
.dlmod downloads/ai_mods/AIDev.py
.dlmod downloads/ai_mods/GiftClaimer.py
```

### 1. `AIContext` — Аналіз переписок
Використовує штучний інтелект (Gemini / Groq) для розуміння контексту чату.
*   `.sum [кількість повідомлень] [питання]` — Генерує підсумок розмови або відповідає на запитання щодо контексту переписки.

### 2. `AIDev` — Нейро-розробник
Вбудований помічник для створення нових модулів.
*   `.gen [опис модуля]` — Напише і автоматично встановить код модуля прямо в Telegram.
*   Підтримує швидку генерацію через `.aim`.

### 3. `GiftClaimer` — Збирач подарунків
Автоматичний, швидкий перехоплювач подарунків у Telegram каналах. Блискавично забирає Telegram Gifts щойно вони з'являються.

> [!TIP]  
> Налаштувати API ключі для ШІ (Gemini/Groq) можна командою `.cfg AIContext` або `.cfg AIDev`.

---

<div align="center">
  <p><i>Розроблено з ❤️ AuthorChe.</i></p>
</div>
