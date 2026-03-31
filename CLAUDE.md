# Slouka — Belarusian Vocabulary Telegram Bot

## Project Overview

Telegram bot for learning Belarusian vocabulary using Anki-style spaced repetition (SM2 algorithm). Users search words via Verbum.by API, save them as flashcards to decks, and review with spaced intervals.

## Architecture

### Layers

```
src/
├── core/           # Config, shared types
├── services/       # Business logic (stateless, each method owns its UoW transaction)
├── infra/
│   ├── db/         # SQLAlchemy models, repositories, UoW
│   ├── verbum/     # External API client + HTML parser
│   ├── schemas/    # Pydantic models (API responses, parsed data)
│   └── tg/         # Telegram layer (aiogram handlers, aiogram-dialog dialogs, middleware)
├── worker/         # Taskiq broker, scheduler, periodic tasks
└── dependencies/   # Dishka DI providers
```

### Core Layer Rules

`core/` contains implementation-independent logic: config, algorithms (SM2). If it doesn't depend on any external library or infrastructure — it belongs in core.

### Key Patterns

- **Unit of Work**: Every service method opens its own `async with self._uow:` block. UoW auto-commits on success, rollbacks on exception. Never pass UoW around without context manager.
- **Repository pattern**: Generic `BaseRepository[T: Base]` with CRUD. Specific repos extend it (e.g., `CardRepository.get_due_cards`).
- **DI via Dishka**: Services at REQUEST scope, infra clients at APP scope. Dialog callbacks use `@inject` decorator + `FromDishka[ServiceType]` parameter annotation.
- **No DTOs**: Pydantic schemas in `infra/schemas/` are used directly everywhere. Serialize with `.model_dump()` for dialog_data.

### Telegram Layer (aiogram + aiogram-dialog)

- All dialog states in `infra/tg/dialogs/states.py`
- Shared dialog helpers (navigation, predicates, callback factories) live in `infra/tg/dialogs/common.py`
- Dialog callbacks get services via `@inject` + `FromDishka[ServiceType]` (dishka-aiogram-dialog integration)
- `UserMiddleware` auto-registers users on every update
- FSM storage: Redis (requires `DefaultKeyBuilder(with_destiny=True)` for aiogram-dialog compatibility)
- Onboarding is mandatory — checked via `User.onboarding_completed` field

### Verbum.by API

- Endpoint: `GET {VERBUM_URL}/search?q={word}&in={dict_ids}&page=1`
- Returns JSON with `Articles[]`, each containing HTML in `Content` field
- Dictionaries (priority order): `tsblm2022` (explanatory 2022), `tsbm` (explanatory 1977-84), `klyshka` (synonyms), `rbs10` (Russian-Belarusian)
- Each dictionary has its own parser class in `infra/verbum/parser.py`; common post-processing in `VerbumParser._build_card()`
- `VerbumService.search_word()` filters results by headword match and sorts by dictionary priority
- Explanatory parser skips: `<table>` (grammar tables), `<highlight>` (search markers), `<strong class="hw-alt">` (feminine forms), content after `||` separator

### Card Deduplication

Cards are unique per `(deck_id, word)`. `CardService.create_card` returns `None` if duplicate.

### Scheduled Notifications (Taskiq)

- **Broker**: `RedisStreamBroker` on Redis DB index `/2` (index `/0` = FSM storage, `/1` = app Redis)
- **Scheduler**: `TaskiqScheduler` with `LabelScheduleSource`, runs as separate Docker service (single instance only)
- **Worker**: Separate Docker service, runs tasks with Dishka DI (container initialized on `WORKER_STARTUP` event)
- **Dishka integration**: `setup_dishka(container, broker)` adds middleware; tasks use `@broker.task` then `@inject(patch_module=True)` with `FromDishka[T]` params
- **Cron task** `send_review_notifications`: runs every hour, queries users with due cards, filters by timezone + notification_hour, sends Telegram message
- **User model fields**: `notifications_enabled` (bool), `notification_hour` (int, local time 0-23), `timezone` (str, IANA like `Europe/Minsk`)
- **Edge cases**: `TelegramForbiddenError` auto-disables notifications; `TelegramRetryAfter` retries once after sleep
- Worker uses its own `BotProvider` (APP scope) — safe because it only calls `send_message`, not polling

## Tech Stack

- Python 3.14, aiogram 3.x, aiogram-dialog 2.x, SQLAlchemy 2.x (async), Dishka, Pydantic, aiohttp
- Taskiq + taskiq-redis (scheduled tasks, background worker)
- PostgreSQL 17, Redis (FSM storage + taskiq broker)
- uv for dependency management, ruff for linting, mypy (strict) for type checking
- Docker Compose with base + dev overlay pattern (5 services: database, redis, bot, worker, scheduler)
- GitHub Actions CI: ruff check + ruff format + mypy on push/PR to main

## Commands

All commands run from `bot/` directory:

```sh
uv run ruff check src/         # Lint
uv run ruff format src/        # Format
uv run mypy src/               # Type check
```

From project root:

```sh
make dev                       # Start dev environment
make down                      # Stop
make logs                      # Follow logs
make migration m="description" # Generate alembic migration
make migrate                   # Apply migrations
```

## Rules

- All interface text in Belarusian
- Always run `ruff check`, `ruff format`, and `mypy` before committing
- Use `uv add --group dev` for dev dependencies, not `--dev`
- Signed commits (`git commit -S`), no Co-Authored-By
