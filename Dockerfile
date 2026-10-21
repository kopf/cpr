FROM python:3.15-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/cpr/.venv/bin:$PATH"

WORKDIR /cpr

COPY pyproject.toml uv.lock .python-version ./

RUN uv sync --locked --no-dev --no-cache

COPY . /cpr

ARG CPR_BUILD_VER

ENV CPR_VERSION=$CPR_BUILD_VER

# tini as PID 1 forwards signals; a bare Python PID 1 ignores SIGTERM until its handler is set
ENTRYPOINT ["/usr/bin/tini", "--", "python", "/cpr"]