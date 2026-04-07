# Slouka

Тэлеграм-бот для вывучэння беларускай лексікі з дапамогай інтэрвальнага паўтарэння. Шукай словы ў слоўніках [Verbum.by](https://verbum.by), захоўвай іх як карткі ў калоды і паўтарай па алгарытму SM2.

## Магчымасці

- **Пошук слоў** — пошук па чатырох слоўніках Verbum.by (тлумачальны 2022, тлумачальны 1977-84, сінонімы Клышкі, руска-беларускі)
- **Калоды і карткі** — стварэнне калод, дадаванне картак з вынікаў пошуку, прагляд, выдаленне
- **Інтэрвальнае паўтарэнне** — паўтарэнне картак па алгарытму SM2 з ацэнкамі "Дрэнна / Цяжка / Нармалёва / Лёгка"
- **Статыстыка калод** — колькасць картак, новыя, гатовыя да паўтарэння
- **Скід прагрэсу** — магчымасць скінуць прагрэс вывучэння для асобнай карткі
- **Напамінкі** — рэгулярныя апавяшчэнні пра карткі для паўтарэння з наладкай часу і часавой зоны
- **Часавыя зоны** — вызначэнне па GPS-лакацыі або пошук па назве горада
- **Анбордзінг** — пакрокавае знаёмства з ботам для новых карыстальнікаў

## Архітэктура

```
src/
├── core/           # Канфігурацыя, алгарытм SM2, часавыя зоны
├── services/       # Бізнес-логіка (карткі, калоды, пошук, апавяшчэнні)
├── infra/
│   ├── db/         # SQLAlchemy мадэлі, рэпазіторыі, Unit of Work
│   ├── verbum/     # HTTP-кліент і HTML-парсер Verbum.by
│   ├── schemas/    # Pydantic-мадэлі
│   └── tg/         # Telegram: хэндлеры, дыялогі (aiogram-dialog), мідлвэры
├── worker/         # Taskiq: чарга задач, планіроўшчык, перыядычныя задачы
└── dependencies/   # Dishka: правайдэры залежнасцей
```

**Асноўныя патэрны:**

- **Unit of Work** — кожны метад сэрвісу адкрывае ўласную транзакцыю, аўта-каміт пры поспеху, адкат пры памылцы
- **Repository** — базавы `BaseRepository[T]` з CRUD, спецыялізаваныя рэпазіторыі для складаных запытаў
- **Dependency Injection** — Dishka з `REQUEST` і `APP` скоўпамі
- **Dialog FSM** — aiogram-dialog для шматкрокавых дыялогаў з карыстальнікам

## Устаноўка і запуск

### Патрабаванні

- Docker і Docker Compose
- [uv](https://docs.astral.sh/uv/) (для лакальнай распрацоўкі)

### Зменныя асяроддзя

Стварыце файл `bot/.env`:

```env
TELEGRAM__TOKEN=your-telegram-bot-token
DATABASE__URL=postgresql+asyncpg://user:password@database:5432/dbname
VERBUM__URL=https://verbum.by/api
REDIS__URL=redis://redis:6379/0
```

І ў корані праекта (для Docker Compose):

```env
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=dbname
```

### Запуск

```sh
make dev          # Запусціць dev-асяроддзе
make down         # Спыніць
make logs         # Логі
make migrate      # Прымяніць міграцыі
```

## Распрацоўка

```sh
cd bot
uv run ruff check src tests     # Лінтэр
uv run ruff format src tests    # Фарматаванне
uv run mypy src                 # Праверка тыпаў
uv run pytest tests -v          # Тэсты (патрабуе Docker для testcontainers)
```

Міграцыі базы:

```sh
make migration m="апісанне"     # Згенераваць новую міграцыю
make migrate                    # Прымяніць
make migrate-down               # Адкаціць апошнюю
```

Тэсты выкарыстоўваюць рэальны PostgreSQL праз testcontainers — SQLite не выкарыстоўваецца.

## Планы развіцця

Ідэі і планы збіраюцца ў [Issues](https://github.com/MarkCesium/Slouka/issues). Калі ёсць прапанова — стварыце issue.

## Як далучыцца

*Coming soon*

## Тэхналогіі

Python 3.14 · aiogram 3 · aiogram-dialog 2 · SQLAlchemy 2 (async) · Dishka · Pydantic 2 · aiohttp · Taskiq · PostgreSQL 17 · Redis · Docker Compose · ruff · mypy · pytest · testcontainers
