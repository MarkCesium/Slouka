FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

WORKDIR /bot

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=never

RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /bot
RUN uv sync --locked --no-dev

ENV PATH="/bot/.venv/bin:$PATH"

ENTRYPOINT []

USER nonroot

CMD ["sh", "-c", "alembic upgrade head && python -m src.main"]
