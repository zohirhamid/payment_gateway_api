from enum import Enum


class PaymentIntentStatus(str, Enum):
    '''
    later we will add:
        requires_action
        refunded
        requires_capture
        partially_refunded
    '''
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"