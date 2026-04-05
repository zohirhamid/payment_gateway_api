from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import model modules (not symbols) so SQLAlchemy registers tables on Base.metadata,
# while avoiding circular imports (models import Base).
import app.db.models.merchant  # noqa: F401
import app.db.models.payment_intent # noqa
import app.db.models.charge #noqa
import app.db.models.idempotency_record #noqa
import app.db.models.webhook_event #noqa