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


settings = Settings()
