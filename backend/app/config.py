from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://huan:huan123@postgres:5432/huan"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Zitadel
    zitadel_url: str = "https://your-zitadel-instance.com"
    zitadel_client_id: str = ""
    zitadel_client_secret: str = ""
    # Note: redirect_uri should point to frontend callback, not backend
    # Frontend handles the OAuth callback and sends the code to backend
    zitadel_redirect_uri: str = "http://localhost:3000/auth/callback"

    # JWT
    secret_key: str = "your-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Spark
    spark_master_url: str = "spark://spark-master:7077"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
