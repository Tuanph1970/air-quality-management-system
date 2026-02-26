"""FastAPI application and route registration."""
from fastapi import FastAPI

app = FastAPI(
    title="Alert Service",
    description="Alerts and violations microservice",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "alert-service"}
