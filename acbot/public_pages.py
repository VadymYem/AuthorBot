# ©️ AuthorChe · AuthorBot
"""Shared, localized Rich Message pages for onboarding and the companion bot."""

from html import escape

from .translations import SUPPORTED_LANGUAGES, normalize_language, translator

PAGES = ("start", "help", "about", "author", "projects")
GITHUB = "https://github.com/VadymYem/AuthorBot"
WEBSITE = "https://authorche.top"
TELEGRAM = "https://t.me/wsinfo"


def text(key: str, language: str = "en") -> str:
    language = normalize_language(language)
    key = f"public_pages.{key}"
    return translator.data.get(language, {}).get(key) or translator.data["en"][key]


def heading(title: str, subtitle: str = "") -> str:
    # Telegram headings have no alignment field. Pull quotations are centered
    # natively; arbitrary CSS/align attributes on h1 would not center the title.
    credit = f"<cite>{subtitle}</cite>" if subtitle else ""
    return f"<aside><b>{title}</b>{credit}</aside>"


def buttons(language: str) -> str:
    return (
        '<tg-button-row align="center">'
        f'<tg-button type="url" style="primary" url="{GITHUB}">GitHub</tg-button>'
        f'<tg-button type="url" style="success" url="{WEBSITE}/ubot.html">{text("install", language)}</tg-button>'
        '</tg-button-row><tg-button-row align="center">'
        f'<tg-button type="url" url="{WEBSITE}">authorche.top</tg-button>'
        f'<tg-button type="url" url="{TELEGRAM}">Telegram</tg-button>'
        '</tg-button-row>'
    )


def command_table(language: str) -> str:
    rows = "".join(
        f'<tr><td><code>/{page}</code></td><td>{text(page + "_label", language)}</td></tr>'
        for page in PAGES
    )
    return f'<table bordered striped compact>{rows}</table>'


def first_steps(language: str, prefix: str = ".") -> str:
    prefix = escape(prefix)
    rows = "".join(
        f'<tr><td><code>{prefix}{command}</code></td><td>{text(key, language)}</td></tr>'
        for command, key in (
            ("help", "step_help"), ("help &lt;module&gt;", "step_module"),
            ("dlmod &lt;url&gt;", "step_install"), ("loadmod", "step_file"),
            ("setlang", "step_language"), ("info", "step_info"),
        )
    )
    return heading(text("first_steps", language)) + f'<table bordered striped compact>{rows}</table>'


def rich_page(page: str, language: str = "en", *, prefix: str = ".") -> str:
    if page not in (*PAGES, "welcome"):
        raise ValueError("Unknown public page")
    t = lambda key: text(key, language)
    title = "AuthorBot" if page in {"start", "welcome", "about"} else t(page + "_label")
    content = [heading(title, "by AuthorChe"), '<hr/>']
    if page in {"start", "welcome", "about", "author"}:
        artwork = "author_artwork" if page == "author" else "bot_artwork"
        caption = "AuthorChe" if page == "author" else "AuthorBot · by AuthorChe"
        content.append(f'<figure><img src="tg://photo?id={artwork}"/><figcaption>{caption}</figcaption></figure>')

    if page in {"start", "welcome"}:
        content += [heading(t("welcome_title")), f'<p>{t("welcome_intro" if page == "welcome" else "start_intro")}</p>']
        content.append(heading(t("possibilities")))
        content.append('<ul>' + ''.join(f'<li>{t(key)}</li>' for key in ("feature_modules", "feature_inline", "feature_rich", "feature_control")) + '</ul>')
        if page == "welcome":
            content += [first_steps(language, prefix), f'<blockquote>{t("choose_language")}</blockquote>']
        else:
            content += [heading(t("explore")), command_table(language)]
    elif page == "help":
        content += [f'<p>{t("help_intro")}</p>', command_table(language), first_steps(language, prefix), f'<blockquote expandable>{t("help_note")}</blockquote>']
    elif page == "about":
        content += [heading(t("about_tagline")), f'<p>{t("about_intro")}</p>', f'<p>{t("about_workflow")}</p>', heading(t("possibilities"))]
        content.append('<table bordered striped compact>' + ''.join(
            f'<tr><td><b>{t("about_" + key + "_title")}</b></td><td>{t("about_" + key)}</td></tr>'
            for key in ("modules", "inline", "rich", "security", "backup", "language")
        ) + '</table>')
        content += [f'<details open><summary>{t("about_setup_title")}</summary><p>{t("about_setup")}</p></details>', f'<blockquote>{t("about_vision")}</blockquote>', f'<p>{t("author_hint")}</p>']
    elif page == "author":
        content += [heading("AuthorChe", t("author_tagline")), f'<p>{t("author_intro")}</p>', f'<p>{t("author_vision")}</p>', heading(t("author_world")), f'<p>{t("author_projects")}</p>']
    elif page == "projects":
        content += [f'<p>{t("projects_intro")}</p>']
        for name, key in (("AuthorGram", "project_gram"), ("AuthorBot", "project_bot"), ("Jarvis | AuthorAi", "project_ai"), ("Goose | AuthorBrowser", "project_browser"), ("Author AI", "project_platform")):
            content += [heading(name), f'<p>{t(key)}</p>']
            if key == "project_gram":
                content.append('<tg-button-row align="center"><tg-button type="url" style="success" url="https://play.google.com/store/apps/details?id=toss.authorgram.apk">Google Play</tg-button><tg-button type="url" url="https://t.me/authorgram_apk">Telegram</tg-button></tg-button-row>')

    content += ['<hr/>', buttons(language), '<footer>AuthorBot · by AuthorChe</footer>']
    return '\n'.join(content)


def fallback_page(page: str, language: str = "en", *, prefix: str = ".") -> str:
    """Classic Bot API HTML only, for clients without Rich Message support."""
    t = lambda key: text(key, language)
    if page in {"start", "welcome"}:
        body = t("welcome_intro" if page == "welcome" else "start_intro")
    elif page == "about":
        body = t("about_intro") + '\n\n' + t("about_workflow")
        body += '\n\n' + '\n'.join(f'• {t("about_" + key + "_title")}: {t("about_" + key)}' for key in ("modules", "inline", "rich", "security", "backup", "language"))
    elif page == "author":
        body = t("author_intro") + '\n\n' + t("author_vision")
    elif page == "projects":
        body = '\n'.join(f'• {t(key)}' for key in ("project_gram", "project_bot", "project_ai", "project_browser", "project_platform"))
    else:
        body = t("help_intro")
    commands = '\n'.join(f'/{key} — {t(key + "_label")}' for key in PAGES)
    if page in {"welcome", "help"}:
        commands += '\n\n' + t("first_steps") + '\n' + '\n'.join(
            f'<code>{escape(prefix)}{cmd}</code> — {t(key)}' for cmd, key in (("help", "step_help"), ("setlang", "step_language"), ("dlmod &lt;url&gt;", "step_install"))
        )
    title = 'AuthorChe' if page == 'author' else 'AuthorBot'
    return f'<b>{title}</b> · by AuthorChe\n\n{body}\n\n{commands}\n\n{WEBSITE}\n{TELEGRAM}\n{GITHUB}'


def bot_commands(language: str = "en") -> list:
    return [{"command": page, "description": text(page + "_label", language)} for page in PAGES]
