# AuthorBot Security Policy

## Security model

AuthorBot operates with the privileges of the Telegram account that installs it. Core modules therefore follow a strict rule: no hidden owner escalation, no secret logging, and no external control channel enabled by default.

## Secrets

The project must never commit or log:

- Telegram API hash;
- BotFather bot token;
- Telegram session/auth key;
- passwords or 2FA values;
- third-party API keys.

BotFather responses that can contain a token are deliberately redacted from debug logs.

## Database

Local DB snapshots are written atomically. The previous valid snapshot is retained as a `.bak` file. When Redis is configured but unavailable, AuthorBot falls back to the local snapshot instead of starting with an empty remote state.

## External modules

External Python modules are executable code. Install only modules whose source you trust.

Primary module repository:

```text
https://github.com/hikariatama/host/raw/master
```

## Reporting

- https://t.me/wsinfo
- https://authorche.top

Do not include live tokens, session files, passwords, API hashes or private database dumps in public issues.


## Web setup

The web UI is always protected with HTTP Basic authentication, including after a Telegram account has been initialized. Telegram confirmation is an additional authorization layer, not a replacement for HTTP authentication. AuthorBot generates a high-entropy startup password when `AUTHORBOT_WEB_PASSWORD` is not configured.

Docker publishes the web UI on `127.0.0.1` by default. External binding must be enabled explicitly. Browser session cookies are HttpOnly, SameSite=Strict, time-limited, and marked Secure when the request is delivered over HTTPS.

## Debugger

The traceback viewer is bound to `127.0.0.1` only and Werkzeug interactive evaluation is disabled. It does not create a public reverse tunnel and cannot execute Python expressions from the browser.

## Module repository credentials

Loader Basic Auth credentials are sent only to the configured primary module repository. They are never forwarded automatically to additional repositories or arbitrary module URLs.
