from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.auth_service import AuthService

class AuthMiddleware(BaseHTTPMiddleware):
    PUBLIC_ROUTES = ["/", "/health", "/login", "/signup", "/ask", "/upload", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.PUBLIC_ROUTES:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")

        token = auth_header.replace("Bearer ", "")
        payload = AuthService.decode_access_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        request.state.user = payload
        return await call_next(request)
