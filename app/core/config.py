from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./symphony.db"
    HF_TOKEN: str = ""
    AUTHENTICATION_TOKEN: str = ""
    JULES_API_URL: str = "https://harvesthealth-chat-app.hf.space"
    PLANDEX_API_URL: str = "https://auxteam-plandex.hf.space"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
