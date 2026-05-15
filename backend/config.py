from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Переименовано или оставлено для обратной совместимости клиента
    hh_user_agent: str = "ResumeMarketValue/1.0 (hackathon@tbank.local)"

    # ИСПРАВЛЕНО: Базовый URL изменен на API Работа России
    hh_base_url: str = "http://opendata.trudvsem.ru/api/v1"

    vacancies_per_fetch: int = 100
    use_mock_on_hh_failure: bool = True


settings = Settings()
