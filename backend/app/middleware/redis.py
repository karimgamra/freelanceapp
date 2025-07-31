from redis import Redis
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
import json


redis = Redis(host="localhost", port=6379, decode_responses=True)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        path = request.url.path

        if path == "/app/api/v1/users/login":
            key = f"rate:{ip}:login"
            count = redis.get(key)

            if count and int(count) >= 5:
                raise HTTPException(
                    status_code=429,
                    detail="Too many login attempts. Try again in a minute.",
                )

            pipe = redis.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, 60)  # 60 seconds window
            pipe.execute()

        return await call_next(request)


def make_cache_key(path: str, query_params: dict) -> str:
    query_string = json.dumps(query_params, sort_keys=True)
    raw_key = f"{path}?{query_string}"
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    return f"cache:{hashed_key}"
