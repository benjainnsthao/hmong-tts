"""Same-origin browser boundary for the trusted local service."""

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class LocalBrowserBoundary:
    def __init__(self, app: ASGIApp, *, host: str, port: int) -> None:
        self.app = app
        names = {host, "localhost"}
        self.authorities = {
            f"{('[' + name + ']') if ':' in name else name}:{port}" for name in names
        }
        if port == 80:
            self.authorities.update(names)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        host = headers.get("host", "").lower()
        origins = headers.getlist("origin")
        allowed = (
            len(headers.getlist("host")) == 1
            and host in self.authorities
            and len(origins) <= 1
            and (not origins or origins[0] == f"http://{host}")
            and headers.get("sec-fetch-site", "none") in {"none", "same-origin"}
        )
        if scope["method"] == "POST":
            allowed = allowed and headers.get("content-type", "").split(";")[0] == (
                "application/json"
            )

        async def protected_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                outgoing = MutableHeaders(scope=message)
                outgoing["Cache-Control"] = "no-store"
                outgoing["X-Content-Type-Options"] = "nosniff"
                outgoing["Referrer-Policy"] = "no-referrer"
                outgoing["Cross-Origin-Resource-Policy"] = "same-origin"
                outgoing["X-Frame-Options"] = "DENY"
                outgoing["Content-Security-Policy"] = (
                    "default-src 'none'; script-src 'self'; style-src 'self'; "
                    "connect-src 'self'; media-src 'self'; img-src 'self'; "
                    "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
                )
            await send(message)

        if not allowed:
            response = JSONResponse(
                {
                    "status": "failure",
                    "category": "browser_request_rejected",
                    "message": "Open the local dashboard URL printed by the server.",
                },
                status_code=403,
            )
            await response(scope, receive, protected_send)
            return
        await self.app(scope, receive, protected_send)
