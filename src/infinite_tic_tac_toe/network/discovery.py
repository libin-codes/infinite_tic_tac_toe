"""LAN Room discovery using UDP broadcast beacons and 4-character room codes."""

from __future__ import annotations

import json
import random
import socket
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

DISCOVERY_PORT = 37020
BEACON_MAGIC = "ITTT_LAN"
CODE_CHARACTERS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # excludes 0, O, 1, I


def generate_room_code(length: int = 4) -> str:
    """Generate a clean, unambiguous uppercase room code."""
    return "".join(random.choices(CODE_CHARACTERS, k=length))


@dataclass(frozen=True)
class RoomBeacon:
    code: str
    host_name: str
    tcp_port: int
    host_mark: str

    def to_json(self) -> str:
        return json.dumps({
            "magic": BEACON_MAGIC,
            "code": self.code.upper(),
            "name": self.host_name,
            "port": self.tcp_port,
            "mark": self.host_mark,
        })

    @classmethod
    def from_json(cls, data_str: str) -> Optional["RoomBeacon"]:
        try:
            d = json.loads(data_str)
            if d.get("magic") == BEACON_MAGIC:
                return cls(
                    code=str(d["code"]).upper(),
                    host_name=str(d.get("name", "Host")),
                    tcp_port=int(d["port"]),
                    host_mark=str(d.get("mark", "X")),
                )
        except Exception:
            pass
        return None


class LanBroadcaster:
    """Periodically broadcasts a UDP beacon on the LAN notifying clients of the room."""

    def __init__(self, beacon: RoomBeacon, port: int = DISCOVERY_PORT, interval: float = 1.0) -> None:
        self.beacon = beacon
        self.port = port
        self.interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
            self._thread = None

    def _run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Allow reuse if supported
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass

        payload = self.beacon.to_json().encode("utf-8")
        broadcast_addrs = ("255.255.255.255", "<broadcast>", "127.0.0.1")

        while self._running:
            for addr in broadcast_addrs:
                try:
                    sock.sendto(payload, (addr, self.port))
                except Exception:
                    pass
            time.sleep(self.interval)
        try:
            sock.close()
        except Exception:
            pass


class LanScanner:
    """Listens for UDP beacons to match a 4-character room code."""

    def __init__(
        self,
        target_code: str,
        on_found: Callable[[str, int, RoomBeacon], None],
        port: int = DISCOVERY_PORT,
    ) -> None:
        self.target_code = target_code.strip().upper()
        self.on_found = on_found
        self.port = port
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
            self._thread = None

    def _run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass
        sock.settimeout(0.5)

        try:
            sock.bind(("", self.port))
        except Exception:
            # If bind fails, try 127.0.0.1
            try:
                sock.bind(("127.0.0.1", self.port))
            except Exception:
                return

        while self._running:
            try:
                data, addr = sock.recvfrom(2048)
                beacon = RoomBeacon.from_json(data.decode("utf-8", errors="ignore"))
                if beacon and beacon.code == self.target_code:
                    host_ip = addr[0]
                    self.on_found(host_ip, beacon.tcp_port, beacon)
                    break
            except socket.timeout:
                continue
            except Exception:
                break

        try:
            sock.close()
        except Exception:
            pass
