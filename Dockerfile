FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    DOCKER=1 \
    PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR /data/AuthorBot

# Copy dependency files first
COPY poetry.lock pyproject.toml ./

# Install project dependencies globally (since virtualenvs-create=false)
RUN /opt/poetry/bin/poetry lock --no-update && /opt/poetry/bin/poetry install --only main --no-root

# Copy the rest of the application
COPY . .

# Expose the API port
EXPOSE 8080

CMD ["python3", "-m", "hikka", "--root"]
