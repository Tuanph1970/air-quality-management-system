"""FastAPI application and route registration."""
from fastapi import FastAPI

app = FastAPI(
    title="Sensor Service",
    description="Sensor and readings microservice",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sensor-service"}
