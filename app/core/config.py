from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Payment Gateway API"
    app_version: str = "0.1.0"
    app_description: str = "A Stripe-like payment gateway built with FastAPI for learning purposes."
    database_url: str = "sqlite:///./payment_gateway.db"
    WINDOW_SECONDS: int = 60

settings = Settings()
