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
