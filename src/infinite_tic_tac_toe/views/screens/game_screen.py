"""Game screen housing the sidebar, divider, board view, and round banner."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, Optional

from infinite_tic_tac_toe.models.game import InfiniteTicTacToeLogic
from infinite_tic_tac_toe.views.board.view import BoardView
from infinite_tic_tac_toe.views.components.banner import RoundBanner
from infinite_tic_tac_toe.views.components.sidebar import Sidebar, SidebarActions
from infinite_tic_tac_toe.views.theme import ButtonStyle, FontBook, Palette


class GameScreen(tk.Frame):
    """Container for the active game: sidebar, board area, and round banner."""

    SIDEBAR_WEIGHT = 2
    MAIN_WEIGHT = 5
    BANNER_TOP = 0.04

    def __init__(
        self,
        parent: tk.Misc,
        palette: Palette,
        fonts: FontBook,
        styles: Dict[str, ButtonStyle],
        game: InfiniteTicTacToeLogic,
        sidebar_actions: SidebarActions,
        on_cell_click: Callable[[int, int], None],
    ) -> None:
        super().__init__(parent, bg=palette.bg)
        self._palette = palette
        self._fonts = fonts
        self._styles = styles
        self._game = game
        self._sidebar_actions = sidebar_actions
        self._on_cell_click = on_cell_click

        self._build_layout()

    def _build_layout(self) -> None:
        p = self._palette

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=self.SIDEBAR_WEIGHT, uniform="panes")
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=self.MAIN_WEIGHT, uniform="panes")

        # Sidebar
        self.sidebar = Sidebar(
            self,
            p,
            self._fonts,
            self._styles,
            self._sidebar_actions,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Vertical Divider
        tk.Frame(self, bg=p.divider, width=1).grid(row=0, column=1, sticky="ns")

        # Main Area
        self.main_area = tk.Frame(self, bg=p.bg)
        self.main_area.grid(row=0, column=2, sticky="nsew")

        # Board View
        self.board_view = BoardView(self.main_area, self._game, p, self._on_cell_click)
        self.board_view.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Round Banner (floats at top)
        self.banner = RoundBanner(self.main_area, p, self._fonts)
        self.banner.place(relx=0.5, rely=self.BANNER_TOP, anchor="n")

    def redraw_widgets(self) -> None:
        self.sidebar.redraw_buttons()
        self.banner.redraw()
