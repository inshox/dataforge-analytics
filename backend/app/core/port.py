"""Resolve a free listen port when the default is occupied."""

from __future__ import annotations

import logging
import os
import socket

logger = logging.getLogger(__name__)


def is_port_available(host: str, port: int) -> bool:
    """Return True if we can bind to host:port (port is free)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def find_listen_port(host: str = "127.0.0.1", preferred: int = 8000, max_tries: int = 10) -> int:
    """Pick preferred port or the next free port in range."""
    for offset in range(max_tries):
        port = preferred + offset
        if is_port_available(host, port):
            if offset > 0:
                logger.warning(
                    "Port %s is in use; using %s instead",
                    preferred,
                    port,
                )
            return port
    raise RuntimeError(
        f"No free port in range {preferred}–{preferred + max_tries - 1} on {host}"
    )


def ensure_port_env(host: str = "127.0.0.1", preferred: int = 8000) -> int:
    """Set PORT in os.environ if unset; return resolved port."""
    if os.environ.get("PORT"):
        try:
            return int(os.environ["PORT"])
        except ValueError:
            pass
    port = find_listen_port(host, preferred)
    os.environ["PORT"] = str(port)
    return port


def write_port_file(data_dir, port: int) -> None:
    from pathlib import Path

    path = Path(data_dir) / "backend.port"
    path.write_text(str(port), encoding="utf-8")
