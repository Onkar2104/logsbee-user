from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gmail_address: str = ""
    gmail_app_password: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465

    # meta_access_token: str = ""
    # meta_phone_number_id: str = ""
    # meta_graph_api_version: str = ""
    # whatsapp_otp_template_name: str = ""
    # whatsapp_otp_language: str = "en_US"

    otp_hash_secret: str = ""
    otp_expiry_seconds: int = 300
    otp_resend_cooldown_seconds: int = 60
    otp_max_attempts: int = 5

    # Lock an account for this many minutes after repeated wrong passwords.
    login_max_failed_attempts: int = 5
    login_attempt_window_seconds: int = 900
    login_lockout_minutes: int = 15

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Comma-separated browser origins allowed to call this API.
    cors_origins: str = ""


settings = Settings()
