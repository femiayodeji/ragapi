FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    build-essential \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install --no-cache-dir uv
RUN uv pip install --system --no-cache .

RUN mkdir -p /app/piper && \
    ARCH=$(uname -m) && \
    OS=$(uname -s | tr '[:upper:]' '[:lower:]') && \
    if [ "$OS" = "darwin" ]; then \
        PIPER_FILE="piper_macos_x86_64.tar.gz"; \
    else \
        if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then \
            PIPER_FILE="piper_linux_aarch64.tar.gz"; \
        else \
            PIPER_FILE="piper_linux_x86_64.tar.gz"; \
        fi; \
    fi && \
    wget -q https://github.com/rhasspy/piper/releases/download/2023.11.14-2/$PIPER_FILE && \
    tar -xzf $PIPER_FILE -C /app/piper/ && \
    rm $PIPER_FILE && \
    chmod +x /app/piper/piper/piper

ENV LD_LIBRARY_PATH=/app/piper:$LD_LIBRARY_PATH
ENV ESPEAK_DATA_PATH=/app/piper/espeak-ng-data

RUN /app/piper/piper/piper --version

COPY *.py ./
COPY data/ data/
COPY .env* ./

RUN mkdir -p data/documents voices storage/chroma_db && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

RUN if [ ! -f voices/en_US-lessac-medium.onnx ]; then \
    cd voices && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json; \
    fi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]