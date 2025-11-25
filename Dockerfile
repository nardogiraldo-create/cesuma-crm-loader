FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# ---- FIX: asegurar chromedriver en /usr/bin ----
RUN set -eux; \
    if [ -f /usr/lib/chromium/chromedriver ]; then ln -sf /usr/lib/chromium/chromedriver /usr/bin/chromedriver; fi; \
    if [ -f /usr/lib/chromium-browser/chromedriver ]; then ln -sf /usr/lib/chromium-browser/chromedriver /usr/bin/chromedriver; fi; \
    if [ -f /usr/lib/chromedriver/chromedriver ]; then ln -sf /usr/lib/chromedriver/chromedriver /usr/bin/chromedriver; fi; \
    chmod +x /usr/bin/chromedriver || true

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

RUN echo "Chrome -> $(which chromium)"; chromium --version; \
    echo "Driver -> $(which chromedriver)"; chromedriver --version

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["gunicorn", "app:app", "--workers", "1", "--timeout", "120", "--bind", "0.0.0.0:10000"]
