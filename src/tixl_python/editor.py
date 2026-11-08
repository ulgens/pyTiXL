"""Locating, launching, and owning the TiXL editor."""

import contextlib
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import TextIO

from tixl_python.client import TixlClient, try_connect
from tixl_python.config import DEFAULT_PORT, STARTUP_TIMEOUT_SECONDS

log = logging.getLogger(__name__)


def find_tixl(explicit: str | None) -> Path | None:
    """Find the TiXL executable, preferring an explicit path."""
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_file() else None

    env_path = os.environ.get("TIXL_EXE")
    if env_path and Path(env_path).expanduser().is_file():
        return Path(env_path).expanduser()

    candidates: list[Path] = []
    for base in (Path.cwd(), Path(__file__).resolve().parent):
        for directory in (base, *base.parents):
            candidates += [
                directory / "Editor" / "bin" / "Debug" / "net10.0" / "TiXL",
                directory / "Editor" / "bin" / "Debug" / "net10.0" / "TiXL.exe",
                directory / "Editor" / "bin" / "Release" / "net10.0" / "TiXL",
                directory / "Editor" / "bin" / "Release" / "net10.0" / "TiXL.exe",
            ]

    if sys.platform == "darwin":
        candidates += [
            Path("/Applications/TiXL.app/Contents/MacOS/TiXL"),
            Path.home() / "Applications" / "TiXL.app" / "Contents" / "MacOS" / "TiXL",
        ]
    elif os.name == "nt":
        for env_var in ("ProgramFiles", "LOCALAPPDATA"):
            base = os.environ.get(env_var)
            if base:
                candidates += [
                    Path(base) / "TiXL" / "TiXL.exe",
                    Path(base) / "TiXL" / "Player.exe",
                ]
    else:
        candidates += [
            Path("/opt/TiXL/TiXL"),
            Path("/usr/local/bin/TiXL"),
            Path.home() / ".local" / "share" / "TiXL" / "TiXL",
        ]

    for name in ("TiXL", "tixl"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def app_bundle_for(exe: Path) -> Path | None:
    """Return the enclosing .app bundle for a macOS executable, if any."""
    for parent in exe.parents:
        if parent.suffix == ".app":
            return parent
    return None


def wait_for_port(port: int, timeout: float) -> TixlClient | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        client = try_connect(port, timeout=0.5)
        if client is not None:
            client.pump(30)
            return client
        time.sleep(1.0)
    return None


def launch_editor(
    exe: Path,
    port: int,
    window: str | None,
    log_dir: Path,
) -> tuple[TixlClient, subprocess.Popen | None, TextIO | None, Path | None]:
    """Launch TiXL with the debug bridge and wait until it answers."""
    args = [
        "--debug-server",
        str(port),
        "--no-splash",
        "--no-reopen",
    ]
    if window:
        args += ["--window", window]

    # On macOS, LaunchServices gives TiXL its own TCC permissions. A process
    # spawned directly from a terminal can be denied access to ~/Documents.
    if sys.platform == "darwin":
        app = app_bundle_for(exe)
        if app is not None:
            log.info("Launching: open -n -a %s --args %s", app, " ".join(args))
            subprocess.run(["open", "-n", "-a", str(app), "--args", *args], check=True)
            client = wait_for_port(port, STARTUP_TIMEOUT_SECONDS)
            if client is None:
                raise RuntimeError(f"TiXL did not open the debug port {port} within {STARTUP_TIMEOUT_SECONDS}s.")
            return client, None, None, None

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "tixl-editor.log"
    log_file = log_path.open("w", encoding="utf-8")
    cmd = [str(exe), *args]
    log.info("Launching: %s", " ".join(cmd))
    process = subprocess.Popen(
        cmd,
        cwd=str(exe.parent),
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    deadline = time.time() + STARTUP_TIMEOUT_SECONDS
    while time.time() < deadline:
        if process.poll() is not None:
            log_file.flush()
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            raise RuntimeError(f"TiXL exited during startup (code {process.returncode}).\n{tail}")

        client = try_connect(port, timeout=0.5)
        if client is not None:
            client.pump(30)
            return client, process, log_file, log_path

        time.sleep(1)

    process.terminate()
    log_file.close()
    raise RuntimeError(f"TiXL did not open the debug port {port} within {STARTUP_TIMEOUT_SECONDS}s. See {log_path}")


class EditorSession:
    """A connection to TiXL, launching the editor if no debug server is listening.

    Sessions are context managers. Only an editor launched by the session is
    shut down on exit; an already-running editor is left alone.
    """

    def __init__(
        self,
        *,
        port: int = DEFAULT_PORT,
        executable: str | Path | None = None,
        window: str | None = None,
        log_dir: str | Path | None = None,
    ):
        self.port = port
        self.executable = Path(executable).expanduser() if executable else None
        self.window = window
        self.log_dir = Path(log_dir) if log_dir else Path.cwd()
        self.client: TixlClient | None = None
        self.launched = False
        self.log_path: Path | None = None
        self._process: subprocess.Popen | None = None
        self._log_file: TextIO | None = None

    def open(self) -> TixlClient:
        """Attach to a running editor or launch one, returning the client."""
        if self.client is not None:
            return self.client

        client = try_connect(self.port, timeout=1.0)
        if client is not None:
            log.info("Attached to TiXL on 127.0.0.1:%s", self.port)
            self.client = client
            return client

        exe = find_tixl(str(self.executable) if self.executable else None)
        if exe is None:
            raise RuntimeError(
                f"Could not find TiXL and nothing is listening on 127.0.0.1:{self.port}.\n"
                "Start TiXL with --debug-server, or pass an explicit executable."
            )

        log.info("Using TiXL: %s", exe)
        (
            self.client,
            self._process,
            self._log_file,
            self.log_path,
        ) = launch_editor(exe, self.port, self.window, self.log_dir)
        self.launched = True
        return self.client

    def close(self, *, keep_open: bool = False) -> None:
        """Close the connection and, if this session launched it, the editor."""
        if self.client is None:
            return

        if self.launched and not keep_open:
            log.info("Shutting down TiXL...")
            with contextlib.suppress(Exception):
                self.client.send_only("shutdown")
            if self._process is not None:
                try:
                    self._process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    self._process.terminate()

        self.client.close()
        self.client = None
        self.launched = False
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None

    def __enter__(self) -> EditorSession:
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
