import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_id = request.client.host if request.client else "unknown"

        if request.url.path == "/ask":
            now = time.time()
            self.requests[client_id] = [t for t in self.requests[client_id] if now - t < 60]

            if len(self.requests[client_id]) >= settings.RATE_LIMIT_PER_MINUTE:
                raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a moment.")

            self.requests[client_id].append(now)

        return await call_next(request)
