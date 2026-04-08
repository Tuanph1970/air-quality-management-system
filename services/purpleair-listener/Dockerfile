FROM python:3.11-slim

WORKDIR /app

# Install wget for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends wget && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/

EXPOSE 8012

EXPOSE 8012

# Run the listener (health server runs alongside via asyncio.gather in main())
CMD ["python", "-m", "uvicorn", "src.listener:app", "--host", "0.0.0.0", "--port", "8012"]