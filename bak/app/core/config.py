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
    secret_key: str = Field(..., alias="SECRET_KEY")
    admin_email: str = Field("", alias="ADMIN_EMAIL")
    admin_password: str = Field("", alias="ADMIN_PASSWORD")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    database_url: str = Field("postgresql://postgres:postgres@db:5432/alanko", alias="DATABASE_URL")
    minio_internal_url: str = Field("minio:9000", alias="MINIO_INTERNAL_URL")
    minio_public_url: str = Field("http://localhost:9000", alias="MINIO_PUBLIC_URL")
    minio_access_key: str = Field(..., alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(..., alias="MINIO_SECRET_KEY")
    yookassa_shop_id: str = Field("", alias="YOOKASSA_SHOP_ID")
    yookassa_secret_key: str = Field("", alias="YOOKASSA_SECRET_KEY")
    yookassa_return_url: str = Field("", alias="YOOKASSA_RETURN_URL")
    consultation_default_duration_minutes: int = Field(60, alias="PRIVATE_CONSULTATION_DEFAULT_DURATION_MINUTES")
    consultation_max_capacity: int = Field(4, alias="PRIVATE_CONSULTATION_MAX_CAPACITY")
    consultation_booking_open_days: int = Field(30, alias="PRIVATE_CONSULTATION_BOOKING_OPEN_DAYS")
    consultation_cancel_cutoff_hours: int = Field(24, alias="PRIVATE_CONSULTATION_CANCEL_CUTOFF_HOURS")
    consultations_allow_overlapping_slots: bool = Field(False, alias="PRIVATE_CONSULTATIONS_ALLOW_OVERLAPPING_SLOTS")
    consultation_default_price: int = Field(0, alias="PRIVATE_CONSULTATION_DEFAULT_PRICE")
    consultation_timezone: str = Field("Asia/Yekaterinburg", alias="CONSULTATION_TIMEZONE")


settings = Settings()
