FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright + aiomysql
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers (Python package, after pip install)
RUN pip install playwright && playwright install chromium --with-deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Playwright browser installed above

EXPOSE 8011

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8011"]
