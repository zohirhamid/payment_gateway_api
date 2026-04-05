"""FastAPI application entrypoint.

What this module does:
- Creates the FastAPI app with metadata from settings.
- Registers API routers.
- Ensures DB tables exist for this MVP via SQLAlchemy metadata.

Returns:
    The `app` object, imported by the ASGI server.
"""

from fastapi import FastAPI

from app.api.routes.auth_debug import router as auth_debug_router
from app.api.routes.merchants import router as merchants_router
from app.api.routes.payment_intents import router as payment_intents_router
from app.api.routes.webhooks import router as webhooks_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)

# Add security scheme for Swagger UI authorize button.
# This enables an "Authorize" modal that sends `Authorization: Bearer <token>`.
app.openapi_components = {  # type: ignore
    "securitySchemes": {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
}

# Create all tables for all registered models if they do not already exist.
Base.metadata.create_all(bind=engine)

app.include_router(auth_debug_router)
app.include_router(merchants_router)
app.include_router(payment_intents_router)
app.include_router(webhooks_router)
