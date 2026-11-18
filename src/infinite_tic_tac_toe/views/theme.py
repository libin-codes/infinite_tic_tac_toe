"""Theme, colors, fonts, and button styling presets for Infinite Tic-Tac-Toe."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from typing import Dict, Literal, Optional, Tuple

from infinite_tic_tac_toe.models.game import Cell

FontWeight = Literal["normal", "bold"]

GRID_SIZE = 3
DEFAULT_WINDOW = (1400, 900)  # Reference size used for font scaling
MIN_WINDOW = (1050, 650)


@dataclass(frozen=True)
class Palette:
    """All colours used by the UI."""

    bg: str = "#13141f"
    sidebar: str = "#181926"
    surface: str = "#1e1f2e"
    surface_light: str = "#282a3d"
    surface_light_hover: str = "#383a54"
    divider: str = "#26273b"

    card_active: str = "#25273b"
    card_inactive: str = "#191a27"
    card_border: str = "#2d2f44"

    cell: str = "#242538"
    cell_hover: str = "#2f314c"
    grid_line: str = "#383952"

    text: str = "#e2e8f0"
    text_muted: str = "#94a3b8"
    text_dim: str = "#64748b"

    accent: str = "#2563eb"
    accent_hover: str = "#1d4ed8"

    x: str = "#38bdf8"
    o: str = "#f43f5e"
    x_strike: str = "#0284c7"
    o_strike: str = "#e11d48"
    x_avatar: str = "#0c4a6e"
    o_avatar: str = "#3d0c18"

    gold: str = "#fbbf24"
    input_bg: str = "#181926"
    input_border: str = "#2d2f44"
    input_focus: str = "#38bdf8"

    confetti: Tuple[str, ...] = (
        "#38bdf8", "#f43f5e", "#fbbf24", "#34d399",
        "#a78bfa", "#f472b6", "#60a5fa", "#fde047",
    )

    def mark_color(self, player: str) -> str:
        return self.x if player == "X" else self.o

    def strike_color(self, player: str) -> str:
        return self.x_strike if player == "X" else self.o_strike

    def avatar_bg(self, player: str) -> str:
        return self.x_avatar if player == "X" else self.o_avatar


PALETTE = Palette()


class FontBook:
    """Named fonts that are rescaled together when the window size changes."""

    FAMILY = "Helvetica"
    MIN_SIZE = 7
    SPECS: Dict[str, Tuple[int, FontWeight]] = {
        "eyebrow": (12, "bold"),
        "title": (17, "bold"),
        "section": (10, "bold"),
        "player_name": (12, "bold"),
        "status_active": (9, "bold"),
        "status_idle": (9, "normal"),
        "badge": (20, "bold"),
        "avatar": (24, "bold"),
        "button_primary": (11, "bold"),
        "button_secondary": (10, "bold"),
        "button_muted": (10, "normal"),
        "button_large": (15, "bold"),
        "button_huge": (17, "bold"),
        "round": (18, "bold"),
        "dialog_title": (14, "bold"),
        "dialog_heading": (10, "bold"),
        "dialog_body": (9, "normal"),
        # New Menu & Lobby Fonts
        "menu_title": (32, "bold"),
        "menu_subtitle": (13, "normal"),
        "card_title": (15, "bold"),
        "card_desc": (11, "normal"),
        "input_text": (13, "bold"),
        "input_large": (14, "bold"),
        "code_display": (28, "bold"),
        "link": (10, "normal"),
    }

    def __init__(self, root: tk.Misc) -> None:
        self._fonts: Dict[str, tkfont.Font] = {
            name: tkfont.Font(root=root, family=self.FAMILY, size=size, weight=weight)
            for name, (size, weight) in self.SPECS.items()
        }

    def __getitem__(self, name: str) -> tkfont.Font:
        return self._fonts[name]

    def rescale(self, factor: float) -> None:
        for name, (base_size, _) in self.SPECS.items():
            self._fonts[name].configure(size=max(self.MIN_SIZE, round(base_size * factor)))

    def line_height(self, name: str) -> int:
        return int(self._fonts[name].metrics("linespace"))


@dataclass(frozen=True)
class ButtonStyle:
    bg: str
    hover: str
    fg: str
    font: str  # name inside FontBook
    disabled_bg: Optional[str] = None
    disabled_fg: Optional[str] = None
    border: Optional[str] = None
    hover_border: Optional[str] = None
    border_width: int = 1


def build_button_styles(p: Palette) -> Dict[str, ButtonStyle]:
    slate_grey_style = ButtonStyle(
        bg=p.surface_light,             # "#282a3d"
        hover=p.surface_light_hover,     # "#383a54"
        fg="white",
        font="button_huge",
        disabled_bg=p.surface,           # "#1e1f2e"
        disabled_fg="#4b5563",
        border=p.grid_line,              # "#383952"
        hover_border=p.x,                # "#38bdf8"
        border_width=2,
    )

    lobby_button_style = ButtonStyle(
        bg=p.surface_light,             # "#282a3d"
        hover=p.surface_light_hover,     # "#383a54"
        fg="white",
        font="button_large",
        disabled_bg=p.surface,           # "#1e1f2e"
        disabled_fg="#4b5563",
        border=p.grid_line,              # "#383952"
        hover_border=p.x,                # "#38bdf8"
        border_width=2,
    )

    return {
        "primary": ButtonStyle(
            p.accent,
            p.accent_hover,
            "white",
            "button_primary",
            disabled_bg="#1d2238",
            disabled_fg="#4b5563",
        ),
        "secondary": ButtonStyle(
            p.surface_light,
            p.surface_light_hover,
            p.text,
            "button_secondary",
            disabled_bg=p.surface,
            disabled_fg="#4b5563",
        ),
        "muted": ButtonStyle(
            p.surface_light,
            p.surface_light_hover,
            p.text_muted,
            "button_muted",
            disabled_bg=p.surface,
            disabled_fg="#4b5563",
        ),
        "cyan": ButtonStyle(
            "#0284c7",
            "#0369a1",
            "white",
            "button_primary",
            disabled_bg="#1d2238",
            disabled_fg="#4b5563",
        ),
        "menu_primary": slate_grey_style,
        "menu_secondary": slate_grey_style,
        "lobby_action": lobby_button_style,
    }
