"""Canvas-based button with hover, border, and custom corner radius support."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Dict, Optional

from infinite_tic_tac_toe.views.drawing import draw_rounded_rect
from infinite_tic_tac_toe.views.theme import ButtonStyle, FontBook


class RoundedButton(tk.Canvas):
    """Canvas button with smooth rounded or sharp rectangular corners and hover states."""

    RADIUS_RATIO = 0.28

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command: Optional[Callable[[], None]],
        style: ButtonStyle,
        fonts: FontBook,
        parent_bg: str,
        height: Optional[int] = None,
        width: Optional[int] = None,
        corner_radius: Optional[float] = None,
        border_color: Optional[str] = None,
        hover_border_color: Optional[str] = None,
        border_width: Optional[int] = None,
    ) -> None:
        options: Dict[str, Any] = {"highlightthickness": 0, "cursor": "hand2", "bg": parent_bg}
        if height:
            options["height"] = height
        if width:
            options["width"] = width
        super().__init__(parent, **options)

        self._text = text
        self._command = command
        self._style = style
        self._fonts = fonts
        self._current_bg = style.bg
        self._corner_radius = corner_radius
        self._border_color = border_color
        self._hover_border_color = hover_border_color
        self._border_width = border_width
        self._is_hovered = False
        self._enabled = True

        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", lambda e: self._on_click())

    def _on_click(self) -> None:
        if self._enabled and self._command:
            self._command()

    def _set_hover(self, hovering: bool) -> None:
        if not self._enabled:
            return
        self._is_hovered = hovering
        self._current_bg = self._style.hover if hovering else self._style.bg
        self.redraw()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        if self._enabled == enabled:
            return
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "")
        self._current_bg = self._style.bg if enabled else (self._style.disabled_bg or self._style.bg)
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 2 or h <= 2:
            return
        bg = self._current_bg if self._enabled else (self._style.disabled_bg or self._style.bg)
        fg = self._style.fg if self._enabled else (self._style.disabled_fg or self._style.fg)

        border = (
            (self._hover_border_color if self._is_hovered else self._border_color)
            or (self._style.hover_border if self._is_hovered else self._style.border)
            or ""
        )
        border_w = self._border_width if self._border_width is not None else getattr(self._style, "border_width", 1)

        radius = self._corner_radius if self._corner_radius is not None else (h * self.RADIUS_RATIO)
        if radius <= 0:
            self.create_rectangle(1, 1, w - 1, h - 1, fill=bg, outline=border, width=border_w)
        else:
            draw_rounded_rect(self, 1, 1, w - 1, h - 1, radius=radius, fill=bg, outline=border, width=border_w)

        self.create_text(w / 2, h / 2, text=self._text, fill=fg, font=self._fonts[self._style.font])
