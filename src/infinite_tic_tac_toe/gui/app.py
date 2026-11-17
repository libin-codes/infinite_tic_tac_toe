"""Main application controller wiring game logic to views and user interactions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional

from infinite_tic_tac_toe.gui.board import BoardView
from infinite_tic_tac_toe.gui.sidebar import Sidebar, SidebarActions
from infinite_tic_tac_toe.gui.theme import (
    DEFAULT_WINDOW,
    MIN_WINDOW,
    PALETTE,
    FontBook,
    build_button_styles,
)
from infinite_tic_tac_toe.gui.widgets import RoundBanner, RulesDialog
from infinite_tic_tac_toe.logic import InfiniteTicTacToeLogic


class InfiniteTicTacToeApp:
    """Main window: owns the game and scores and wires them to the views."""

    # Pane proportions (grid weights): sidebar 2 : board area 5  (~29% / 71%)
    SIDEBAR_WEIGHT = 2
    MAIN_WEIGHT = 5

    # Floating round banner: distance from the top as a fraction of window height
    BANNER_TOP = 0.04

    # Font scaling
    MIN_SCALE = 0.7
    MAX_SCALE = 1.2
    SCALE_EPSILON = 0.02

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.palette = PALETTE
        self.game = InfiniteTicTacToeLogic()
        self.scores: Dict[str, int] = {"X": 0, "O": 0}
        self.round_number = 1
        self.is_fullscreen = False
        self._scale = 1.0

        self._configure_window()
        self.fonts = FontBook(root)
        self.styles = build_button_styles(self.palette)

        self._build_layout()
        self._bind_events()
        self._refresh_all()

    # -- window --------------------------------------------------------------

    def _configure_window(self) -> None:
        self.root.title("Infinite Tic-Tac-Toe")
        self.root.geometry(f"{DEFAULT_WINDOW[0]}x{DEFAULT_WINDOW[1]}")
        self.root.minsize(*MIN_WINDOW)
        self.root.configure(bg=self.palette.bg)

        try:
            self.root.attributes("-zoomed", True)  # Linux
        except tk.TclError:
            try:
                self.root.state("zoomed")  # Windows
            except tk.TclError:
                sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                self.root.geometry(f"{sw}x{sh}+0+0")

    def _toggle_fullscreen(self, event: Optional[tk.Event] = None) -> None:
        self._set_fullscreen(not self.is_fullscreen)

    def _exit_fullscreen(self, event: Optional[tk.Event] = None) -> None:
        if self.is_fullscreen:
            self._set_fullscreen(False)

    def _set_fullscreen(self, enabled: bool) -> None:
        self.is_fullscreen = enabled
        try:
            self.root.attributes("-fullscreen", enabled)
        except tk.TclError:
            pass

    # -- layout --------------------------------------------------------------

    def _build_layout(self) -> None:
        root = self.root
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=self.SIDEBAR_WEIGHT, uniform="panes")
        root.grid_columnconfigure(1, weight=0)
        root.grid_columnconfigure(2, weight=self.MAIN_WEIGHT, uniform="panes")

        self.sidebar = Sidebar(
            root, self.palette, self.fonts, self.styles,
            SidebarActions(
                new_round=self.on_new_round,
                reset_scores=self.on_reset_all,
                show_rules=self.show_rules,
                toggle_fullscreen=self._toggle_fullscreen,
            ),
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        tk.Frame(root, bg=self.palette.divider, width=1).grid(row=0, column=1, sticky="ns")

        self.main_area = tk.Frame(root, bg=self.palette.bg)
        self.main_area.grid(row=0, column=2, sticky="nsew")

        self.board_view = BoardView(self.main_area, self.game, self.palette, self._handle_cell_click)
        self.board_view.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Created after the board so it floats above it.
        self.banner = RoundBanner(self.main_area, self.palette, self.fonts)
        self.banner.place(relx=0.5, rely=self.BANNER_TOP, anchor="n")

    def _bind_events(self) -> None:
        self.root.bind("<r>", lambda e: self.on_new_round())
        self.root.bind("<R>", lambda e: self.on_new_round())
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)
        self.root.bind("<Configure>", self._on_root_configure)

    def _on_root_configure(self, event: tk.Event) -> None:
        """Rescale all fonts proportionally to the window size."""
        if event.widget is not self.root:
            return
        factor = min(event.width / DEFAULT_WINDOW[0], event.height / DEFAULT_WINDOW[1])
        factor = max(self.MIN_SCALE, min(self.MAX_SCALE, factor))
        if abs(factor - self._scale) < self.SCALE_EPSILON:
            return

        self._scale = factor
        self.fonts.rescale(factor)
        self.sidebar.redraw_buttons()
        self.banner.redraw()

    # -- view updates --------------------------------------------------------

    def _refresh_all(self) -> None:
        self.sidebar.update_players(self.game, self.scores)
        self.sidebar.set_button_enabled("new_round", not self.game.is_empty)
        self._show_round()
        self.board_view.render()

    def _show_round(self) -> None:
        self.banner.set(f"ROUND {self.round_number}")

    def _show_winner(self, winner: str) -> None:
        self.banner.set(f"PLAYER {winner} WINS ROUND {self.round_number}!")

    # -- game flow -----------------------------------------------------------

    def _handle_cell_click(self, r: int, c: int) -> None:
        if not self.game.is_valid_move(r, c):
            return

        result = self.game.make_move(r, c)
        if not result["success"]:
            return

        if result["vanished"]:
            self.board_view.play_vanish(tuple(result["vanished"]), result["player"])

        if result["game_over"]:
            winner = result["winner"]
            self.scores[winner] += 1
            self.sidebar.update_players(self.game, self.scores)
            self._show_winner(winner)
            self.board_view.play_win()
        else:
            self.sidebar.update_players(self.game, self.scores)
            self._show_round()
        self.sidebar.set_button_enabled("new_round", not self.game.is_empty)
        self.board_view.render()

    def on_new_round(self) -> None:
        if self.game.is_empty:
            return

        if not self.game.game_over:
            if not messagebox.askyesno(
                "New Round",
                "A game is currently in progress. Are you sure you want to start a new round?",
                parent=self.root,
            ):
                return

        self.round_number += 1
        self.game.reset(alternate_starting=True)
        self.board_view.clear_effects()
        self._refresh_all()

    def on_reset_all(self) -> None:
        has_progress = self.round_number > 1 or any(self.scores.values())
        if has_progress and not messagebox.askyesno(
            "Reset Scores",
            "Are you sure you want to reset all scores and start over?",
            parent=self.root,
        ):
            return

        self.scores = {"X": 0, "O": 0}
        self.round_number = 1
        self.game.reset(alternate_starting=False)
        self.board_view.clear_effects()
        self._refresh_all()

    def show_rules(self) -> None:
        RulesDialog(self.root, self.palette, self.fonts, self.styles)


def main() -> None:
    root = tk.Tk()
    InfiniteTicTacToeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
