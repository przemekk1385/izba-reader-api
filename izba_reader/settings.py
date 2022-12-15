from pydantic import AnyUrl, BaseSettings, EmailStr


class Settings(BaseSettings):
    ex: int = 8 * 60 * 60  # 8 hours
    browser_url: AnyUrl = "http://localhost:3000"
    redis_url: AnyUrl = "redis://localhost:6379"

    api_key: str
    origins: list[AnyUrl]

    mail_from: EmailStr
    mail_password: str
    mail_port: int
    mail_server: str
    mail_subject: str
    mail_username: str

    environment: str = "production"
    rollbar_access_token: str
