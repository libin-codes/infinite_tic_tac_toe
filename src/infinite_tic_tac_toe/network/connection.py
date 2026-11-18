"""TCP Connection handling and thread-safe message queues for LAN play."""

from __future__ import annotations

import queue
import socket
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

from infinite_tic_tac_toe.network.protocol import (
    MessageType,
    decode_message,
    encode_message,
)


class NetworkConnection:
    """Manages an active two-way TCP connection with incoming message queueing."""

    def __init__(self, sock: socket.socket, is_host: bool) -> None:
        self.sock = sock
        self.is_host = is_host
        self.inbox: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._running = True
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()

    @property
    def is_connected(self) -> bool:
        return self._running

    def send_message(self, msg_type: str, **payload: Any) -> bool:
        """Send a formatted message over the TCP socket."""
        if not self._running:
            return False
        try:
            data = encode_message(msg_type, **payload)
            self.sock.sendall(data)
            return True
        except Exception:
            self.close()
            return False

    def poll_messages(self) -> List[Dict[str, Any]]:
        """Retrieve all currently queued messages on the main UI thread."""
        messages: List[Dict[str, Any]] = []
        while not self.inbox.empty():
            try:
                messages.append(self.inbox.get_nowait())
            except queue.Empty:
                break
        return messages

    def close(self) -> None:
        """Close connection and background reader."""
        self._running = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass

    def _reader_loop(self) -> None:
        buffer = ""
        while self._running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    msg = decode_message(line)
                    if msg:
                        self.inbox.put(msg)
            except Exception:
                break
        self._running = False
        try:
            self.sock.close()
        except Exception:
            pass
        # Put disconnect notice in inbox
        self.inbox.put({"type": MessageType.LEAVE, "reason": "Connection closed"})


class LanHost:
    """Listens for an incoming TCP client connection."""

    def __init__(
        self,
        on_connected: Callable[[NetworkConnection], None],
        preferred_port: int = 0,
    ) -> None:
        self.on_connected = on_connected
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(("", preferred_port))
        self.port: int = self._server_sock.getsockname()[1]
        self._server_sock.listen(1)
        self._server_sock.settimeout(1.0)
        self._running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._running = False
        try:
            self._server_sock.close()
        except Exception:
            pass

    def _accept_loop(self) -> None:
        while self._running:
            try:
                client_sock, _ = self._server_sock.accept()
                conn = NetworkConnection(client_sock, is_host=True)
                self.on_connected(conn)
                break
            except socket.timeout:
                continue
            except Exception:
                break
        try:
            self._server_sock.close()
        except Exception:
            pass


class LanClient:
    """Establishes an outgoing TCP connection to a host."""

    @staticmethod
    def connect(
        host_ip: str,
        port: int,
        timeout: float = 5.0,
    ) -> Optional[NetworkConnection]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host_ip, port))
            sock.settimeout(None)
            return NetworkConnection(sock, is_host=False)
        except Exception:
            return None
