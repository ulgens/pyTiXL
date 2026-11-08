"""Settings for the optional HTTP bridge."""

from dataclasses import dataclass, field
from pathlib import Path

from tixl_python.config import DEFAULT_PORT

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8787
DEFAULT_CAPTURES_DIR = "captures"

_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "0:0:0:0:0:0:0:1"}


@dataclass(frozen=True, slots=True)
class ApiSettings:
    """Everything the HTTP bridge needs to know before it starts."""

    host: str = DEFAULT_API_HOST
    port: int = DEFAULT_API_PORT
    tixl_host: str = DEFAULT_API_HOST
    tixl_port: int = DEFAULT_PORT
    captures_dir: Path = field(default_factory=lambda: Path(DEFAULT_CAPTURES_DIR))
    token: str | None = None
    cors_origins: tuple[str, ...] = ()
    title: str = "TiXL Bridge API"

    @property
    def is_local_bind(self) -> bool:
        return self.host.lower() in _LOCAL_HOSTS

    def validate(self) -> None:
        """Reject unsafe combinations before uvicorn starts listening."""
        if not self.is_local_bind and not self.token:
            raise ValueError(
                f"Refusing to bind {self.host!r} without a token. "
                "Set TIXL_API_TOKEN or pass --token when exposing the API.",
            )

    def resolved_captures_dir(self) -> Path:
        return self.captures_dir.expanduser().resolve()
