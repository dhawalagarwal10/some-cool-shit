import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # api credentials
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # notification settings
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    slack_bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")
    email_sender: str = os.getenv("EMAIL_SENDER", "")
    email_password: str = os.getenv("EMAIL_PASSWORD", "")
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))

    # database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./inventory.db")

    # app configuration
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    forecast_horizon_days: int = int(os.getenv("FORECAST_HORIZON_DAYS", "30"))
    reorder_safety_factor: float = float(os.getenv("REORDER_SAFETY_FACTOR", "1.5"))

    # inventory thresholds
    low_stock_threshold: float = 0.2  # alert when stock < 20% of average demand
    critical_stock_days: int = 7  # critical if stockout predicted within 7 days

    # forecasting parameters
    forecast_confidence_interval: float = 0.95
    min_historical_days: int = 30  # minimum data needed for forecasting

    # purchase order settings
    auto_po_enabled: bool = False  # require approval by default
    min_order_quantity: int = 10
    batch_order_size: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
