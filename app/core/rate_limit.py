'''
This is the main implementation file.

It should contain:

    rule dataclass
    result dataclass
    fixed-window helper functions
    Redis key builder
    merchant subject extraction
    Redis counter check logic
    dependency factory

This file is the engine.
'''


from dataclasses import dataclass

'''
this gives you a clean object for each endpoint rule
example instances later:

scope="create_payment_intent",
limit=5,
window_seconds=60

scope="confirm_payment", limit=10, window_seconds=60
'''
@dataclass(frozen=True)
class RateLimitRule:
    scope: str
    limit: int
    window_seconds: int

@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    current_count: int
    remaining: int
    retry_after: int
    reset_after: int


def get_window_start(now: int, window_seconds: int) -> int:
    return now - (now % window_seconds)