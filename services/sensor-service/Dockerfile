FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["uvicorn", "src.interfaces.api.routes:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
