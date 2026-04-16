""" FastAPI application entrypoint.

What this module does:
- Creates the FastAPI app with metadata from settings.
- Registers API routers.
- Ensures DB tables exist for this MVP via SQLAlchemy metadata.

Returns:
    The `app` object, imported by the ASGI server.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.auth_debug import router as auth_debug_router
from app.api.routes.charges import router as charges_router
from app.api.routes.merchants import router as merchants_router
from app.api.routes.payment_intents import router as payment_intents_router
from app.api.routes.webhooks import router as webhooks_router
from app.api.routes.refunds import router as refunds_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api.error_handlers import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)

register_error_handlers(app)

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

app.include_router(auth_debug_router)
app.include_router(merchants_router)
app.include_router(payment_intents_router)
app.include_router(charges_router)
app.include_router(webhooks_router)
app.include_router(refunds_router)
