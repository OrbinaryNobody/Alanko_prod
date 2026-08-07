from pydantic import Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover - compatibility fallback
    from pydantic import BaseSettings as PydanticBaseSettings

    class SettingsConfigDict(dict):
        pass

    class BaseSettings(PydanticBaseSettings):
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"


class Settings(BaseSettings):
    if hasattr(BaseSettings, "model_config"):
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"

    app_name: str = "Alanko App"
    secret_key: str = Field("dev-secret-key", alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = Field("postgresql://postgres:postgres@db:5432/alanko", alias="DATABASE_URL")
    minio_internal_url: str = Field("minio:9000", alias="MINIO_INTERNAL_URL")
    minio_public_url: str = Field("http://localhost:9000", alias="MINIO_PUBLIC_URL")
    minio_access_key: str = Field("minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field("minioadmin", alias="MINIO_SECRET_KEY")


settings = Settings()
