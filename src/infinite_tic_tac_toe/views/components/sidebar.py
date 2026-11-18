"""Left sidebar containing title, player cards, and action buttons."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from infinite_tic_tac_toe.models.game import InfiniteTicTacToeLogic
from infinite_tic_tac_toe.views.components.button import RoundedButton
from infinite_tic_tac_toe.views.components.player_card import PlayerCard
from infinite_tic_tac_toe.views.theme import ButtonStyle, FontBook, Palette


@dataclass(frozen=True)
class ButtonSpec:
    label: str
    style: str  # key into build_button_styles()
    action: str  # attribute name on SidebarActions


@dataclass(frozen=True)
class SidebarActions:
    new_round: Callable[[], None]
    reset_scores: Callable[[], None]
    show_rules: Callable[[], None]
    toggle_fullscreen: Callable[[], None]
    leave_game: Optional[Callable[[], None]] = None


class Sidebar(tk.Frame):
    """Left panel: title, player cards and action buttons.

    Every vertical position is a fraction of the sidebar's height, so the
    layout stretches with the window.
    """

    # Layout (fractions of sidebar width / height)
    SIDE_MARGIN = 0.06
    HEADER_HEIGHT = 0.12
    PLAYERS_LABEL_Y = 0.155
    CARD_TOP = 0.19
    CARD_HEIGHT = 0.10
    CARD_STEP = 0.12
    BUTTONS_TOP = 0.68
    BUTTON_HEIGHT = 0.065
    BUTTON_STEP = 0.076

    DEFAULT_BUTTON_SPECS: Tuple[ButtonSpec, ...] = (
        ButtonSpec("🔄 New Round (R)", "primary", "new_round"),
        ButtonSpec("↺ Reset Scores", "secondary", "reset_scores"),
        ButtonSpec("❓ How to Play", "secondary", "show_rules"),
    )

    def __init__(
        self,
        parent: tk.Misc,
        palette: Palette,
        fonts: FontBook,
        styles: Dict[str, ButtonStyle],
        actions: SidebarActions,
    ) -> None:
        super().__init__(parent, bg=palette.sidebar)
        self._palette = palette
        self._fonts = fonts
        self._styles = styles
        self._actions = actions

        self.cards: Dict[str, PlayerCard] = {}
        self.buttons: Dict[str, RoundedButton] = {}
        self._buttons: List[RoundedButton] = []

        self._build_header()
        self._build_players_section()
        self._build_cards()
        self._build_buttons()

    # -- construction --------------------------------------------------------

    def _build_header(self) -> None:
        p, m = self._palette, self.SIDE_MARGIN
        tk.Label(
            self, text="INFINITE", font=self._fonts["eyebrow"], bg=p.sidebar, fg=p.x,
        ).place(relx=m, rely=self.HEADER_HEIGHT * 0.36, anchor="w")
        tk.Label(
            self, text="TIC-TAC-TOE", font=self._fonts["title"], bg=p.sidebar, fg=p.text,
        ).place(relx=m, rely=self.HEADER_HEIGHT * 0.70, anchor="w")
        tk.Frame(self, bg=p.divider).place(relx=0, rely=self.HEADER_HEIGHT, relwidth=1, height=1)

    def _build_players_section(self) -> None:
        p, m = self._palette, self.SIDE_MARGIN
        tk.Label(
            self, text="PLAYERS", font=self._fonts["section"], bg=p.sidebar, fg=p.text_dim,
        ).place(relx=m, rely=self.PLAYERS_LABEL_Y, anchor="w")

    def _build_cards(self) -> None:
        for index, mark in enumerate(("X", "O")):
            card = PlayerCard(self, mark, self._palette, self._fonts)
            card.place(
                relx=self.SIDE_MARGIN,
                rely=self.CARD_TOP + index * self.CARD_STEP,
                relwidth=1 - 2 * self.SIDE_MARGIN,
                relheight=self.CARD_HEIGHT,
            )
            self.cards[mark] = card

    def _build_buttons(self) -> None:
        specs = list(self.DEFAULT_BUTTON_SPECS)
        if self._actions.leave_game:
            specs.append(ButtonSpec("🏠 Main Menu", "muted", "leave_game"))

        for index, spec in enumerate(specs):
            action_fn = getattr(self._actions, spec.action, None)
            if not action_fn:
                continue
            button = RoundedButton(
                self,
                spec.label,
                action_fn,
                self._styles[spec.style],
                self._fonts,
                parent_bg=self._palette.sidebar,
            )
            button.place(
                relx=self.SIDE_MARGIN,
                rely=self.BUTTONS_TOP + index * self.BUTTON_STEP,
                relwidth=1 - 2 * self.SIDE_MARGIN,
                relheight=self.BUTTON_HEIGHT,
            )
            self._buttons.append(button)
            self.buttons[spec.action] = button

    # -- public API ----------------------------------------------------------

    def set_button_enabled(self, action: str, enabled: bool) -> None:
        if action in self.buttons:
            self.buttons[action].set_enabled(enabled)

    def update_player_labels(self, x_name: str = "Player X", o_name: str = "Player O") -> None:
        if "X" in self.cards:
            self.cards["X"]._name.configure(text=x_name)
        if "O" in self.cards:
            self.cards["O"]._name.configure(text=o_name)

    def update_players(self, game: InfiniteTicTacToeLogic, scores: Dict[str, int]) -> None:
        for mark, card in self.cards.items():
            if game.game_over:
                active = game.winner == mark
                status = "🏆 WINNER" if active else "DEFEAT"
            else:
                active = game.current_player == mark
                status = "TURN" if active else "WAITING"
            card.apply(active=active, wins=scores[mark], status=status)

    def redraw_buttons(self) -> None:
        for button in self._buttons:
            button.redraw()
