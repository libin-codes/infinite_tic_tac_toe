"""Canvas-based rounded button with hover and disabled states."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Dict, Optional

from infinite_tic_tac_toe.gui.drawing import draw_rounded_rect
from infinite_tic_tac_toe.gui.theme import ButtonStyle, FontBook


class RoundedButton(tk.Canvas):
    """Canvas button with smooth rounded corners and a hover effect.

    Corner radius is a fraction of the button's own height, so the button
    looks the same at any size. Size it with ``place``/``pack(fill=...)``.
    """

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
        draw_rounded_rect(self, 1, 1, w - 1, h - 1, radius=h * self.RADIUS_RATIO, fill=bg, outline="")
        self.create_text(w / 2, h / 2, text=self._text, fill=fg, font=self._fonts[self._style.font])
