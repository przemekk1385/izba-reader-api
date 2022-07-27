from pydantic import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    ex: int = 8 * 60 * 60  # 8 hours
    redis_url: str = "redis://localhost:6379"

    api_key: str

    mail_from: str
    mail_password: str
    mail_port: int
    mail_server: str
    mail_subject: str
    mail_username: str

    environment: str = "production"
    rollbar_access_token: str
