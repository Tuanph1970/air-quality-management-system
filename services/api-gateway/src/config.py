from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = "your-super-secret-key"
    factory_service_url: str = "http://factory-service:8001"
    sensor_service_url: str = "http://sensor-service:8002"
    alert_service_url: str = "http://alert-service:8003"
    air_quality_service_url: str = "http://air-quality-service:8004"
    user_service_url: str = "http://user-service:8005"

    class Config:
        env_file = ".env"


settings = Settings()
