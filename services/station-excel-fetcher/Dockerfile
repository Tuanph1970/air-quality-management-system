FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright + aiomysql
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    curl \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    tzdata \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/* \
    && cp /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime \
    && echo "Asia/Ho_Chi_Minh" > /etc/timezone

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser (separate RUN so layer is cached & verified)
RUN playwright install chromium

COPY . .

# Run Alembic migrations on every container start so the table always exists
# after a fresh deploy (even if the volume was wiped)
# Ensure the installed alembic package is not shadowed by /app/alembic_migrations
ENV PYTHONPATH=/app
CMD ["sh", "-c", "alembic upgrade head && exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8011"]

EXPOSE 8011
