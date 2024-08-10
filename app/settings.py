import os
from typing import List, Union

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    APP_DESCRIPTION: str
    ALLOWED_ORIGINS: str
    SECRET_KEY: str
    DB_DSN: str
    DEBUG: bool
    ALGORITHM: str
    EXPIRES_IN: int = 5256000
    TOKEN_ISS: str

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

    @property
    def db_dsn(self):
        return f"mysql+aiomysql://{self.DB_DSN}?charset=utf8mb4"

    @staticmethod
    def setup_logging() -> None:
        """Настройка логирования"""
        import yaml
        import logging.config
        with open("logging.yaml", "r") as f:
            config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)

    @staticmethod
    def setup_architecture():
        """Настройка архитектуры приложения"""
        current_dir = os.getcwd()
        if not os.path.exists(f"{current_dir}/logs"):
            print("Creating")
            os.makedirs(f"{current_dir}/logs/debug/")
            os.makedirs(f"{current_dir}/logs/info/")
            os.makedirs(f"{current_dir}/logs/error/")
            os.makedirs(f"{current_dir}/logs/warning/")
        else:
            print("Directories exists")


settings = Settings()
