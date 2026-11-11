"""LAN host discovery over UDP broadcast.

A Unity client broadcasts DISCOVERY_REQUEST to 255.255.255.255:DISCOVERY_PORT.
Every running backend answers (unicast) with a small JSON payload, so players can
pick the host from a list instead of typing its IP. Set DETECTIVE_LAN_DISCOVERY=0
to disable (e.g. in tests or on a public server).
"""

import asyncio
import json
import logging
import os
import socket
from typing import Optional

logger = logging.getLogger("detective-lan")

DISCOVERY_PORT = 47777
DISCOVERY_REQUEST = b"DETECTIVE_DISCOVER_V1"
SERVICE_NAME = "detective-game"

_transport: Optional[asyncio.DatagramTransport] = None


class _DiscoveryProtocol(asyncio.DatagramProtocol):
    def __init__(self, http_port: int):
        self.http_port = http_port
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr) -> None:
        if data.strip() != DISCOVERY_REQUEST or self.transport is None:
            return
        reply = {
            "service": SERVICE_NAME,
            "host_name": socket.gethostname(),
            "http_port": self.http_port,
        }
        self.transport.sendto(json.dumps(reply).encode("utf-8"), addr)


async def start_lan_discovery(http_port: int) -> None:
    """Start answering discovery broadcasts. Never raises: discovery is optional."""
    global _transport
    if os.getenv("DETECTIVE_LAN_DISCOVERY", "1") == "0" or _transport is not None:
        return
    try:
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _DiscoveryProtocol(http_port),
            local_addr=("0.0.0.0", DISCOVERY_PORT),
            allow_broadcast=True,
        )
        _transport = transport
        logger.info(f"LAN discovery listening on UDP {DISCOVERY_PORT} (HTTP port {http_port})")
    except OSError as e:
        logger.warning(f"LAN discovery disabled, cannot bind UDP {DISCOVERY_PORT}: {e}")


def stop_lan_discovery() -> None:
    global _transport
    if _transport is not None:
        _transport.close()
        _transport = None
