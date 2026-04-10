'''
It should contain:
    rule dataclass + 
    result dataclass + 
    fixed-window helper functions 
    Redis key builder 
    merchant subject extraction 
    Redis counter check logic 
    dependency factory 
'''

from dataclasses import dataclass

import time

from fastapi import Depends, HTTPException
from app.db.models.merchant import Merchant
from app.api.deps import get_current_merchant, get_redis
from app.core.config import settings

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

def raise_rate_limit_exceeded(rule: RateLimitRule, result: RateLimitResult) -> None:
    raise HTTPException(
        status_code=429,
        detail={
            "message": "Rate limit exceeded",
            "scope": rule.scope,
            "retry_after": result.retry_after,
        },
        headers={"Retry-After": str(result.retry_after)},
    )


def get_window_start(now: int, window_seconds: int) -> int:
    return now - (now % window_seconds)

def get_window_reset(now: int, window_seconds: int) -> int:
    '''
    computes how many seconds remain before the current window ends '''
    return get_window_start(now, window_seconds) + window_seconds
    
def build_rate_limit_key(scope: str, merchant_id: str, window_start):
    return f"rate_limit:{scope}:merchant:{merchant_id}:{window_start}"

def get_rate_limit_subject(merchant: Merchant = Depends(get_current_merchant)) -> str:
    return str(merchant.id)

def check_rate_limit(redis, now: int, rule: RateLimitRule, merchant: Merchant = Depends(get_current_merchant)) -> RateLimitResult:
    window_start = get_window_start(now, settings.WINDOW_SECONDS)
    retry_after = get_window_reset(now, settings.WINDOW_SECONDS)
    redis_key = build_rate_limit_key(rule.scope, str(merchant.id), window_start)

    current_count = redis.incr(redis_key)

    if current_count == 1:
        redis.expire(redis_key, retry_after)

    allowed = current_count <= rule.limit
    remaining = max(0, rule.limit - current_count)

    return RateLimitResult(
        allowed=allowed,
        limit=rule.limit,
        current_count=current_count,
        remaining=remaining,
        retry_after=retry_after if not allowed else 0,
        reset_after=retry_after
    )


def rate_limit(rule: RateLimitRule):
    def dependency(
        redis=Depends(get_redis), merchant: Merchant = Depends(get_current_merchant)
        )-> RateLimitResult:

        now = int(time.time())
        result = check_rate_limit(redis, now, rule, merchant)

        if not result.allowed:
            raise_rate_limit_exceeded(rule, result)

        return result

    return dependency