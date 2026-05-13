from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    hh_user_agent: str = "ResumeMarketValue/1.0 (hackathon@tbank.local)"
    hh_base_url: str = "https://api.hh.ru"
    vacancies_per_fetch: int = 100
    use_mock_on_hh_failure: bool = True


settings = Settings()
