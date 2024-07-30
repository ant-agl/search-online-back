from typing import List, Union

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    APP_DESCRIPTION: str
    ALLOWED_ORIGINS: str
    SECRET_KEY: str
    API_TOKEN: str
    DEBUG: bool

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def app_config(self) -> dict[str, Union[bool, str]]:
        return {
            "title": self.APP_NAME,
            "version": self.APP_VERSION,
            "description": self.APP_DESCRIPTION,
            "debug": self.DEBUG,
        }

    @property
    def cors_middleware_config(self) -> dict[str, Union[bool, str, list]]:
        return {
            "allow_origins": self.ALLOWED_ORIGIN.split(",")
            if "*" not in self.ALLOWED_ORIGIN else self.ALLOWED_ORIGIN,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
            "allow_credentials": True,
        }


settings = Settings()