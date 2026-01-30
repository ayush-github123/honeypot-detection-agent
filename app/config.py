from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_KEY: str = "dev-secret-key"


settings = Settings()
