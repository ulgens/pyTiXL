"""Bearer-token protection for the optional HTTP bridge."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tixl_python.api.settings import ApiSettings

bearer_scheme = HTTPBearer(auto_error=False, description="Optional unless TIXL_API_TOKEN is set.")


def get_settings(request: Request) -> ApiSettings:
    return request.app.state.settings


def require_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> None:
    """Require the configured bearer token, if there is one."""
    token: str | None = get_settings(request).token
    if not token:
        return

    if credentials is None or not secrets.compare_digest(credentials.credentials, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
