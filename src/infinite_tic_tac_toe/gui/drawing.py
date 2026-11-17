"""Canvas drawing primitives and color manipulation helpers."""

from __future__ import annotations

import tkinter as tk
from typing import Any


def blend_hex_colors(c1: str, c2: str, t: float) -> str:
    """Blend two hex colours. t=0.0 yields c1, t=1.0 yields c2."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    **kwargs: Any,
) -> int:
    """Draw a smooth rounded rectangle on a Tkinter Canvas."""
    radius = max(0.0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius, y1, x1 + radius, y1,
        x2 - radius, y1, x2 - radius, y1,
        x2, y1, x2, y1 + radius,
        x2, y1 + radius, x2, y2 - radius,
        x2, y2 - radius, x2, y2,
        x2 - radius, y2, x2 - radius, y2,
        x1 + radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius,
        x1, y2 - radius, x1, y1 + radius,
        x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def draw_x(canvas: tk.Canvas, cx: float, cy: float, half: float, color: str, width: int) -> None:
    """Draw an 'X' mark centred at (cx, cy)."""
    for sign in (1, -1):
        canvas.create_line(
            cx - half * sign, cy - half, cx + half * sign, cy + half,
            fill=color, width=width, capstyle=tk.ROUND,
        )


def draw_o(canvas: tk.Canvas, cx: float, cy: float, radius: float, color: str, width: int) -> None:
    """Draw an 'O' mark centred at (cx, cy)."""
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=color, width=width)
