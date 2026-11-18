"""Styled input entry widget with rounded borders and placeholder support."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

from infinite_tic_tac_toe.views.theme import FontBook, Palette


class StyledTextInput(tk.Frame):
    """Custom styled text entry with modern border, height padding, and focus highlights."""

    def __init__(
        self,
        parent: tk.Misc,
        palette: Palette,
        fonts: FontBook,
        placeholder: str = "",
        uppercase: bool = False,
        max_length: Optional[int] = None,
        on_change: Optional[Callable[[str], None]] = None,
        font_name: str = "input_text",
        width_chars: int = 20,
        pady: int = 10,
        padx: int = 14,
        justify: str = "left",
    ) -> None:
        super().__init__(parent, bg=palette.input_bg, highlightthickness=1, highlightbackground=palette.input_border)
        self._palette = palette
        self._placeholder = placeholder
        self._uppercase = uppercase
        self._max_length = max_length
        self._on_change = on_change
        self._is_focused = False

        self._var = tk.StringVar()
        self._var.trace_add("write", self._handle_var_change)

        self._entry = tk.Entry(
            self,
            textvariable=self._var,
            bg=palette.input_bg,
            fg=palette.text,
            insertbackground=palette.text,
            font=fonts[font_name],
            bd=0,
            highlightthickness=0,
            width=width_chars,
            justify=justify,
        )
        self._entry.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)

        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)

        self._showing_placeholder = False
        if placeholder:
            self._show_placeholder()

    def _show_placeholder(self) -> None:
        if not self._var.get():
            self._showing_placeholder = True
            self._entry.configure(fg=self._palette.text_dim)
            self._var.set(self._placeholder)

    def _hide_placeholder(self) -> None:
        if self._showing_placeholder:
            self._showing_placeholder = False
            self._entry.configure(fg=self._palette.text)
            self._var.set("")

    def _on_focus_in(self, event: tk.Event) -> None:
        self._is_focused = True
        self.configure(highlightbackground=self._palette.input_focus, highlightthickness=2)
        if self._showing_placeholder:
            self._hide_placeholder()

    def _on_focus_out(self, event: tk.Event) -> None:
        self._is_focused = False
        self.configure(highlightbackground=self._palette.input_border, highlightthickness=1)
        if not self._var.get().strip():
            self._show_placeholder()

    def _handle_var_change(self, *args: object) -> None:
        if self._showing_placeholder:
            return
        val = self._var.get()
        if self._uppercase:
            val = val.upper()
        if self._max_length and len(val) > self._max_length:
            val = val[:self._max_length]
        if val != self._var.get():
            self._var.set(val)
        if self._on_change:
            self._on_change(self.get_value())

    def get_value(self) -> str:
        if self._showing_placeholder:
            return ""
        return self._var.get().strip()

    def set_value(self, text: str) -> None:
        self._hide_placeholder()
        self._var.set(text)

    def set_focus(self) -> None:
        self._entry.focus_set()

    @property
    def locked(self) -> bool:
        return getattr(self, "_locked", False)

    def set_locked(self, locked: bool) -> None:
        self._locked = locked
        if locked:
            self._entry.configure(
                state="readonly",
                bg=self._palette.surface,
                readonlybackground=self._palette.surface,
                fg=self._palette.text_dim,
            )
            self.configure(bg=self._palette.surface, highlightbackground=self._palette.card_border)
        else:
            self._entry.configure(
                state="normal",
                bg=self._palette.input_bg,
                readonlybackground=self._palette.input_bg,
                fg=self._palette.text,
            )
            self.configure(bg=self._palette.input_bg, highlightbackground=self._palette.input_border)
