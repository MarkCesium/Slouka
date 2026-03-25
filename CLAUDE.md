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
└── dependencies/   # Dishka DI providers
```

### Key Patterns

- **Unit of Work**: Every service method opens its own `async with self._uow:` block. UoW auto-commits on success, rollbacks on exception. Never pass UoW around without context manager.
- **Repository pattern**: Generic `BaseRepository[T: Base]` with CRUD. Specific repos extend it (e.g., `CardRepository.get_due_cards`).
- **DI via Dishka**: Services at REQUEST scope, infra clients at APP scope. Use `container()` context in dialog callbacks to get services.
- **No DTOs**: Pydantic schemas in `infra/schemas/` are used directly everywhere. Serialize with `.model_dump()` for dialog_data.

### Telegram Layer (aiogram + aiogram-dialog)

- All dialog states in `infra/tg/dialogs/states.py`
- Dialog callbacks get services via `manager.middleware_data["dishka_container"]`
- `UserMiddleware` auto-registers users on every update
- FSM storage: Redis (requires `DefaultKeyBuilder(with_destiny=True)` for aiogram-dialog compatibility)
- Onboarding is mandatory — checked via `User.onboarding_completed` field

### Verbum.by API

- Endpoint: `GET {VERBUM_URL}/search?q={word}&in={dict_ids}&page=1`
- Returns JSON with `Articles[]`, each containing HTML in `Content` field
- We use `tsblm2022` dictionary only (Belarusian explanatory)
- HTML parser (`infra/verbum/parser.py`) extracts: headword, accent, POS, definitions, examples, phrases
- Parser skips: `<table>` (grammar tables), `<highlight>` (search markers), `<strong class="hw-alt">` (feminine forms), content after `||` separator

### Card Deduplication

Cards are unique per `(deck_id, word)`. `CardService.create_card` returns `None` if duplicate.

## Tech Stack

- Python 3.14, aiogram 3.x, aiogram-dialog 2.x, SQLAlchemy 2.x (async), Dishka, Pydantic, aiohttp
- PostgreSQL 17, Redis (FSM storage)
- uv for dependency management, ruff for linting, mypy (strict) for type checking
- Docker Compose with base + dev overlay pattern

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

- All interface text in English (user translates to Belarusian manually)
- Always run `ruff check`, `ruff format`, and `mypy` before committing
- Use `uv add --group dev` for dev dependencies, not `--dev`
- Signed commits (`git commit -S`), no Co-Authored-By
