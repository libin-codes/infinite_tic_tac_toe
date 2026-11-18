"""Header banner displaying current round number or clean winner announcement."""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from infinite_tic_tac_toe.views.theme import FontBook, Palette


class RoundBanner(tk.Label):
    """Header text that shows the round / winner with no background or border."""

    def __init__(self, parent: tk.Misc, palette: Palette, fonts: FontBook) -> None:
        super().__init__(
            parent,
            bg=palette.bg,
            fg=palette.text,
            font=fonts["round"],
            highlightthickness=0,
        )
        self._palette = palette
        self._fonts = fonts

    def set(self, text: str, color: Optional[str] = None) -> None:
        self.configure(text=text, fg=color or self._palette.text)

    def redraw(self) -> None:
        self.configure(font=self._fonts["round"])
