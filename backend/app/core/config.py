from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    database_url: str
    secret_key: str
    environment: str = "development"
    allowed_origins: str = "http://localhost:5173"
    resend_api_key: str = ""
    email_from: str = "ATOS Soporte <onboarding@resend.dev>"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()
