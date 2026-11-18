"""Views layer: UI components, board renderers, and theme definitions."""

from infinite_tic_tac_toe.views.board import (
    BoardMetrics,
    BoardRenderer,
    BoardView,
    BoardViewState,
    ConfettiParticle,
    VanishEffect,
)
from infinite_tic_tac_toe.views.components import (
    RULES,
    ButtonSpec,
    PlayerCard,
    RoundBanner,
    RoundedButton,
    RulesDialog,
    Sidebar,
    SidebarActions,
)
from infinite_tic_tac_toe.views.drawing import (
    blend_hex_colors,
    draw_o,
    draw_rounded_rect,
    draw_x,
)
from infinite_tic_tac_toe.views.theme import (
    DEFAULT_WINDOW,
    GRID_SIZE,
    MIN_WINDOW,
    PALETTE,
    ButtonStyle,
    FontBook,
    Palette,
    build_button_styles,
)

__all__ = [
    # Theme & Configuration
    "Palette",
    "PALETTE",
    "FontBook",
    "ButtonStyle",
    "build_button_styles",
    "DEFAULT_WINDOW",
    "MIN_WINDOW",
    "GRID_SIZE",
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
    # Components & Widgets
    "RoundedButton",
    "PlayerCard",
    "RoundBanner",
    "RulesDialog",
    "RULES",
    "ButtonSpec",
    "SidebarActions",
    "Sidebar",
]
