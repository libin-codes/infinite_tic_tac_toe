"""Modular widget components for Infinite Tic-Tac-Toe."""

from infinite_tic_tac_toe.gui.widgets.banner import RoundBanner
from infinite_tic_tac_toe.gui.widgets.button import RoundedButton
from infinite_tic_tac_toe.gui.widgets.dialogs import RULES, RulesDialog
from infinite_tic_tac_toe.gui.widgets.player_card import PlayerCard

__all__ = [
    "RoundedButton",
    "PlayerCard",
    "RoundBanner",
    "RulesDialog",
    "RULES",
]
