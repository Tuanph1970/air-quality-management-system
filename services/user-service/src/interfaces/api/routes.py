"""FastAPI application and route registration."""
from fastapi import FastAPI

app = FastAPI(
    title="User Service",
    description="Authentication and user management microservice",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}
