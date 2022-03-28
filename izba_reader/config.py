from pydantic import BaseSettings


class Config(BaseSettings):
    ex: int = 8 * 60 * 60  # 8 hours
    redis_url: str = "redis://localhost:6379"


config = Config()
