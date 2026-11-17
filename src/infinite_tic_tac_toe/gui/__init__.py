"""Tkinter GUI package for Infinite Tic-Tac-Toe.

This package exposes all application components, widgets, board renderers,
and theme definitions with full backward compatibility.
"""

from infinite_tic_tac_toe.gui.app import InfiniteTicTacToeApp, main
from infinite_tic_tac_toe.gui.board import (
    BoardMetrics,
    BoardRenderer,
    BoardView,
    BoardViewState,
    ConfettiParticle,
    VanishEffect,
)
from infinite_tic_tac_toe.gui.drawing import (
    blend_hex_colors,
    draw_o,
    draw_rounded_rect,
    draw_x,
)
from infinite_tic_tac_toe.gui.sidebar import ButtonSpec, Sidebar, SidebarActions
from infinite_tic_tac_toe.gui.theme import (
    DEFAULT_WINDOW,
    GRID_SIZE,
    MIN_WINDOW,
    PALETTE,
    ButtonStyle,
    Cell,
    FontBook,
    Palette,
    build_button_styles,
)
from infinite_tic_tac_toe.gui.widgets import (
    RULES,
    PlayerCard,
    RoundBanner,
    RoundedButton,
    RulesDialog,
)

__all__ = [
    # Application
    "InfiniteTicTacToeApp",
    "main",
    # Theme & Configuration
    "Palette",
    "PALETTE",
    "FontBook",
    "ButtonStyle",
    "build_button_styles",
    "DEFAULT_WINDOW",
    "MIN_WINDOW",
    "GRID_SIZE",
    "Cell",
    # Drawing Helpers
    "blend_hex_colors",
    "draw_rounded_rect",
    "draw_x",
    "draw_o",
    # Board Components
    "BoardMetrics",
    "ConfettiParticle",
    "VanishEffect",
    "BoardViewState",
    "BoardRenderer",
    "BoardView",
    # Widgets
    "RoundedButton",
    "PlayerCard",
    "RoundBanner",
    "RulesDialog",
    "RULES",
    # Sidebar
    "ButtonSpec",
    "SidebarActions",
    "Sidebar",
]
