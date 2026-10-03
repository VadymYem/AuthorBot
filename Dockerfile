FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    DOCKER=1

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    ffmpeg \
    git \
    libcairo2 \
    libffi-dev \
    libjpeg62-turbo-dev \
    libwebp-dev \
    openssh-client \
    openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt optional_requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -r requirements.txt \
    && (python -m pip install -r optional_requirements.txt || true) \
    && python -m pip check

COPY . .

RUN python scripts/selfcheck.py \
    && python scripts/runtimecheck.py \
    && mkdir -p /data \
    && chmod 700 /data

VOLUME ["/data"]
EXPOSE 8080

CMD ["python", "-m", "acbot", "--root", "--data-root", "/data"]
