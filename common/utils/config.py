"""Configuration management."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_debug: bool = True

    # Database
    database_url: str = "mysql+aiomysql://vulnscan:vulnscan@localhost:3306/vulnscan"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10

    # RabbitMQ
    rabbitmq_url: str = "amqp://vulnscan:vulnscan@localhost:5672/vulnscan"
    rabbitmq_exchange: str = "vulnscan"
    rabbitmq_task_queue: str = "scan.tasks"
    rabbitmq_result_queue: str = "scan.results"

    # Scanner
    scanner_max_concurrency: int = 100
    scanner_default_timeout: int = 30
    scanner_rate_limit: int = 100
    scanner_heartbeat_interval: int = 10

    # Security
    security_secret_key: str = "your-secret-key-change-in-production"
    security_token_expire_minutes: int = 60
    security_algorithm: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
