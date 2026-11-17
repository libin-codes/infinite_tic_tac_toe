"""Interactive board view managing canvas sizing, player input, and animation ticks."""

from __future__ import annotations

import math
import random
import tkinter as tk
from typing import Callable, Optional

from infinite_tic_tac_toe.gui.board.effects import BoardViewState, ConfettiParticle, VanishEffect
from infinite_tic_tac_toe.gui.board.metrics import BoardMetrics
from infinite_tic_tac_toe.gui.board.renderer import BoardRenderer
from infinite_tic_tac_toe.gui.theme import GRID_SIZE, Cell, Palette
from infinite_tic_tac_toe.logic import InfiniteTicTacToeLogic


class BoardView(tk.Frame):
    """The game board: sizing, hover/click input and animations.

    The canvas is centred in the available area and sized as a fraction of it,
    leaving a guaranteed margin above the board for the floating round banner.
    """

    # Board footprint inside the available area
    MAX_WIDTH_FRACTION = 0.78
    MAX_HEIGHT_FRACTION = 0.65  # => >= 12% free above and below the board
    RESIZE_TOLERANCE = 0.01  # ignore resizes smaller than this fraction of the side

    REFERENCE_SIDE = 500  # board side that animation speeds were tuned for

    # Animations
    TICK_MS = 33
    PULSE_STEP = 0.15
    VANISH_STEPS = 4
    WIN_LINE_STEP = 0.14
    CONFETTI_COUNT = 55

    def __init__(
        self,
        parent: tk.Misc,
        game: InfiniteTicTacToeLogic,
        palette: Palette,
        on_cell_click: Callable[[int, int], None],
    ) -> None:
        super().__init__(parent, bg=palette.bg)
        self._game = game
        self._palette = palette
        self._on_cell_click = on_cell_click

        self.state = BoardViewState()
        self.metrics = BoardMetrics.for_side(self.REFERENCE_SIDE)
        self._side = self.REFERENCE_SIDE

        self.canvas = tk.Canvas(self, bg=palette.bg, highlightthickness=0, cursor="hand2")
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")
        self.canvas.configure(width=self.metrics.size, height=self.metrics.size)
        self._renderer = BoardRenderer(self.canvas, palette, vanish_steps=self.VANISH_STEPS)

        self.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

        self._tick_job: Optional[str] = self.after(self.TICK_MS, self._tick)

    # -- public API ----------------------------------------------------------

    @property
    def is_busy(self) -> bool:
        return self.state.win_progress < 1.0

    def render(self) -> None:
        self._renderer.render(self._game, self.metrics, self.state)

    def play_vanish(self, cell: Cell, player: str) -> None:
        self.state.vanish = VanishEffect(cell=cell, player=player, step=self.VANISH_STEPS)

    def play_win(self) -> None:
        size = self.metrics.size
        unit = size / self.REFERENCE_SIDE
        self.state.win_progress = 0.0
        self.state.confetti = [
            ConfettiParticle(
                x=size / 2 + random.uniform(-size * 0.3, size * 0.3),
                y=size / 2 + random.uniform(-size * 0.15, size * 0.15),
                bounds_height=size,
                unit=unit,
                colors=self._palette.confetti,
            )
            for _ in range(self.CONFETTI_COUNT)
        ]

    def clear_effects(self) -> None:
        self.state.hovered = None
        self.state.vanish = None
        self.state.confetti = []
        self.state.win_progress = 1.0

    def destroy(self) -> None:
        if self._tick_job is not None:
            self.after_cancel(self._tick_job)
            self._tick_job = None
        super().destroy()

    # -- sizing --------------------------------------------------------------

    def _on_resize(self, event: tk.Event) -> None:
        side = int(min(event.width * self.MAX_WIDTH_FRACTION, event.height * self.MAX_HEIGHT_FRACTION))
        if side <= GRID_SIZE * 4:
            return
        if abs(side - self._side) < side * self.RESIZE_TOLERANCE:
            return

        self._side = side
        self.metrics = BoardMetrics.for_side(side)
        self.canvas.configure(width=self.metrics.size, height=self.metrics.size)
        self.render()

    # -- input ---------------------------------------------------------------

    def _on_motion(self, event: tk.Event) -> None:
        if self._game.game_over:
            return
        cell = self.metrics.cell_at(event.x, event.y)
        if cell != self.state.hovered:
            self.state.hovered = cell
            self.render()

    def _on_leave(self, event: tk.Event) -> None:
        if self.state.hovered is not None:
            self.state.hovered = None
            self.render()

    def _on_click(self, event: tk.Event) -> None:
        if self._game.game_over or self.is_busy:
            return
        cell = self.metrics.cell_at(event.x, event.y)
        if cell is not None:
            self._on_cell_click(*cell)

    # -- animation loop ------------------------------------------------------

    def _tick(self) -> None:
        s = self.state
        s.pulse_phase = (s.pulse_phase + self.PULSE_STEP) % (2 * math.pi)

        dirty = bool(not self._game.game_over and self._game.get_expiring_piece())

        if s.vanish:
            s.vanish.step -= 1
            dirty = True
            if s.vanish.step <= 0:
                s.vanish = None

        if s.win_progress < 1.0:
            s.win_progress = min(1.0, s.win_progress + self.WIN_LINE_STEP)
            dirty = True

        if s.confetti:
            s.confetti = [p for p in s.confetti if p.update()]
            dirty = True

        if dirty:
            self.render()
        self._tick_job = self.after(self.TICK_MS, self._tick)
