import random

def simulate_payment_result() -> str:
    """
    Simulate the outcome of payment processing.

    For this MVP:
    - Most payments succeed
    - Some payments fail

    Returns:
        "succeeded" or "failed"
    """
    return "succeeded" if random.random() < 0.8 else "failed"