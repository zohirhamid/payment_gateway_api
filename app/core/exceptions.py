class AppError(Exception):
    """Base application exception."""


class NotFoundError(AppError):
    """Base not found error."""


class ConflictError(AppError):
    """Base conflict error."""


class ValidationError(AppError):
    """Base validation/business rule error."""


class PaymentIntentNotFoundError(NotFoundError):
    pass


class ChargeNotFoundError(NotFoundError):
    pass


class PaymentIntentStateError(ConflictError):
    pass


class ChargeStateError(ConflictError):
    pass


class IdempotencyConflictError(ConflictError):
    pass


class RefundNotFoundError(NotFoundError):
    pass
