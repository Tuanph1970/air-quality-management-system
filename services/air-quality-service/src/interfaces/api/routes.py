"""FastAPI application and route registration."""
from fastapi import FastAPI

app = FastAPI(
    title="Air Quality Service",
    description="AQI calculation, predictions, and maps microservice",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "air-quality-service"}
