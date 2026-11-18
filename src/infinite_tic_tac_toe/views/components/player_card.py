"""Sidebar player card displaying avatar, turn status, and white win count."""

from __future__ import annotations

import tkinter as tk

from infinite_tic_tac_toe.views.theme import FontBook, Palette


class PlayerCard(tk.Frame):
    """Sidebar card: square avatar with mark X/O, name + status, and bold wins on the right."""

    GAP_RATIO = 0.14  # Inner gap as a fraction of the card height

    def __init__(self, parent: tk.Misc, mark: str, palette: Palette, fonts: FontBook) -> None:
        super().__init__(
            parent,
            bg=palette.card_inactive,
            highlightbackground=palette.card_border,
            highlightthickness=1,
        )
        self._mark = mark
        self._palette = palette
        self._fonts = fonts
        accent = palette.mark_color(mark)

        self._avatar = tk.Frame(self, bg=palette.avatar_bg(mark))
        self._avatar_label = tk.Label(
            self._avatar, text=mark, font=fonts["avatar"], bg=palette.avatar_bg(mark), fg=accent,
        )
        self._avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        self._info = tk.Frame(self, bg=palette.card_inactive)
        self._name = tk.Label(self._info, text=f"Player {mark}", font=fonts["player_name"], anchor="w")
        self._name.pack(anchor="w", pady=(0, 4))
        self._status = tk.Label(self._info, anchor="w")
        self._status.pack(anchor="w")

        self._wins = tk.Label(self, text="0", font=fonts["badge"])

        self._avatar.place(x=0, y=0, relheight=1, width=1)
        self._info.place(rely=0.5, anchor="w")
        self._wins.place(relx=1.0, rely=0.5, anchor="e")
        self.bind("<Configure>", self._layout)

        self.apply(active=False, wins=0, status="WAITING")

    def _layout(self, event: tk.Event) -> None:
        """Keep the avatar square and derive paddings from the card height."""
        height = event.height
        gap = int(height * self.GAP_RATIO)
        self._avatar.place_configure(width=height)
        self._info.place_configure(x=height + gap)
        self._wins.place_configure(x=-gap * 1.5)

    def apply(self, active: bool, wins: int, status: str) -> None:
        p = self._palette
        accent = p.mark_color(self._mark)
        bg = p.card_active if active else p.card_inactive

        self.configure(
            bg=bg,
            highlightbackground=accent if active else p.card_border,
            highlightthickness=2 if active else 1,
        )
        self._info.configure(bg=bg)
        self._name.configure(bg=bg, fg=p.text if active else p.text_muted)
        self._status.configure(
            bg=bg,
            fg=accent if active else p.text_dim,
            font=self._fonts["status_active" if active else "status_idle"],
            text=status,
        )
        self._wins.configure(bg=bg, text=str(wins), fg=p.text)
