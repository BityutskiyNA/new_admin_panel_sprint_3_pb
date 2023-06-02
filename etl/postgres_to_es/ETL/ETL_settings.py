from pydantic import BaseSettings


class Settings_BS(BaseSettings):
    SQL_DATABASE: str
    SQL_USER: str
    SQL_PASSWORD: str
    SQL_HOST: str
    SQL_PORT: str
    EL_HOST: str
    EL_PORT: str
    time_sleep: int
