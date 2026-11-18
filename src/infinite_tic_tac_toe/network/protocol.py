"""JSON-lines protocol specification for Infinite Tic-Tac-Toe LAN multiplayer."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


class MessageType:
    HANDSHAKE = "handshake"
    MOVE = "move"
    NEW_ROUND = "new_round"
    RESET_SCORES = "reset_scores"
    LEAVE = "leave"
    PING = "ping"
    PONG = "pong"


def encode_message(msg_type: str, **payload: Any) -> bytes:
    """Encode a message dict to a UTF-8 newline-terminated JSON payload."""
    data = {"type": msg_type, **payload}
    return (json.dumps(data) + "\n").encode("utf-8")


def decode_message(raw_line: str) -> Optional[Dict[str, Any]]:
    """Decode a single JSON line string into a message dict."""
    raw_line = raw_line.strip()
    if not raw_line:
        return None
    try:
        data = json.loads(raw_line)
        if isinstance(data, dict) and "type" in data:
            return data
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return None
