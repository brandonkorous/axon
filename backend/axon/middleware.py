"""FastAPI middleware for structured logging context."""

from __future__ import annotations

import re

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Matches /api/orgs/{org_id}/...
_ORG_RE = re.compile(r"^/api/orgs/([^/]+)")


class LogContextMiddleware(BaseHTTPMiddleware):
    """Bind ``org_id`` (and optionally ``agent_id``) into structlog context vars.

    Every log line emitted during the request will carry these fields
    automatically — no manual threading required.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint,
    ) -> Response:
        structlog.contextvars.clear_contextvars()

        match = _ORG_RE.match(request.url.path)
        if match:
            structlog.contextvars.bind_contextvars(org_id=match.group(1))

        try:
            return await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
