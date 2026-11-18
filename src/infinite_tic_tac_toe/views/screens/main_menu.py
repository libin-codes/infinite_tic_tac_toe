"""Main Menu screen presenting clean, minimalistic mode selection."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, Optional

from infinite_tic_tac_toe.views.components.button import RoundedButton
from infinite_tic_tac_toe.views.components.dialogs import RulesDialog
from infinite_tic_tac_toe.views.theme import ButtonStyle, FontBook, Palette


class MainMenuScreen(tk.Frame):
    """Minimalistic home screen displaying game brand title, two large slate grey buttons, and rules link."""

    BUTTON_WIDTH = 520
    BUTTON_HEIGHT = 145

    def __init__(
        self,
        parent: tk.Misc,
        palette: Palette,
        fonts: FontBook,
        styles: Dict[str, ButtonStyle],
        on_start_local: Callable[[], None],
        on_start_lan: Callable[[], None],
        on_show_rules: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, bg=palette.bg)
        self._palette = palette
        self._fonts = fonts
        self._styles = styles
        self._on_start_local = on_start_local
        self._on_start_lan = on_start_lan
        self._on_show_rules = on_show_rules

        self._buttons: list[RoundedButton] = []
        self._build_ui()

    def _build_ui(self) -> None:
        p = self._palette
        f = self._fonts

        # Header area at top: stacked brand title without subtitle
        header_frame = tk.Frame(self, bg=p.bg)
        header_frame.pack(side=tk.TOP, pady=(90, 0))

        tk.Label(
            header_frame,
            text="INFINITE",
            font=f["eyebrow"],
            bg=p.bg,
            fg=p.x,
        ).pack()

        tk.Label(
            header_frame,
            text="TIC-TAC-TOE",
            font=f["menu_title"],
            bg=p.bg,
            fg=p.text,
        ).pack(pady=(4, 0))

        # Center area: Two prominent sharp-edged slate grey buttons floating directly on background
        center_frame = tk.Frame(self, bg=p.bg)
        center_frame.pack(expand=True)

        slate_grey_style = self._styles.get("menu_primary", self._styles["secondary"])

        # Button 1: Local Multiplayer
        btn_local = RoundedButton(
            center_frame,
            "Local Multiplayer",
            self._on_start_local,
            slate_grey_style,
            f,
            p.bg,
            height=self.BUTTON_HEIGHT,
            width=self.BUTTON_WIDTH,
            corner_radius=0,
            border_color=slate_grey_style.border,
            hover_border_color=slate_grey_style.hover_border,
            border_width=slate_grey_style.border_width,
        )
        btn_local.pack(pady=(0, 24))
        self._buttons.append(btn_local)

        # Button 2: LAN Multiplayer (identical slate grey style)
        btn_lan = RoundedButton(
            center_frame,
            "LAN Multiplayer",
            self._on_start_lan,
            slate_grey_style,
            f,
            p.bg,
            height=self.BUTTON_HEIGHT,
            width=self.BUTTON_WIDTH,
            corner_radius=0,
            border_color=slate_grey_style.border,
            hover_border_color=slate_grey_style.hover_border,
            border_width=slate_grey_style.border_width,
        )
        btn_lan.pack()
        self._buttons.append(btn_lan)

        # Small link label: How to play that opens the existing RulesDialog modal
        self._rules_link = tk.Label(
            center_frame,
            text="How to play?",
            font=f["link"],
            bg=p.bg,
            fg=p.text_dim,
            cursor="hand2",
        )
        self._rules_link.pack(pady=(32, 0))

        self._rules_link.bind("<Enter>", lambda e: self._rules_link.configure(fg=p.x))
        self._rules_link.bind("<Leave>", lambda e: self._rules_link.configure(fg=p.text_dim))
        self._rules_link.bind("<Button-1>", lambda e: self._open_how_to_play())

    def _open_how_to_play(self) -> None:
        if self._on_show_rules:
            self._on_show_rules()
        else:
            RulesDialog(self.winfo_toplevel(), self._palette, self._fonts, self._styles)

    def redraw_buttons(self) -> None:
        for b in self._buttons:
            b.redraw()
