"""Modular board package for geometry, animation effects, rendering, and view."""

from infinite_tic_tac_toe.gui.board.effects import (
    BoardViewState,
    ConfettiParticle,
    VanishEffect,
)
from infinite_tic_tac_toe.gui.board.metrics import BoardMetrics
from infinite_tic_tac_toe.gui.board.renderer import BoardRenderer
from infinite_tic_tac_toe.gui.board.view import BoardView

__all__ = [
    "BoardMetrics",
    "ConfettiParticle",
    "VanishEffect",
    "BoardViewState",
    "BoardRenderer",
    "BoardView",
]
