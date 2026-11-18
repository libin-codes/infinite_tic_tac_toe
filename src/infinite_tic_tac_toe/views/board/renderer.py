"""Pure Canvas renderer translating board and view state into visual elements."""

from __future__ import annotations

import math
import tkinter as tk
from typing import Any, Dict, Optional, Tuple

from infinite_tic_tac_toe.models.game import Cell, InfiniteTicTacToeLogic
from infinite_tic_tac_toe.views.board.effects import BoardViewState, VanishEffect
from infinite_tic_tac_toe.views.board.metrics import BoardMetrics
from infinite_tic_tac_toe.views.drawing import blend_hex_colors, draw_o, draw_rounded_rect, draw_x
from infinite_tic_tac_toe.views.theme import GRID_SIZE, Palette

DEFAULT_VANISH_STEPS = 4


class BoardRenderer:
    """Pure drawing: turns game + view state into canvas items."""

    # Look of a mark by age: 3 = newest, 1 = oldest (about to vanish)
    FADE_BY_AGE = {3: 1.0, 2: 0.65, 1: 0.32}
    STROKE_BY_AGE = {3: 1.0, 2: 0.8, 1: 0.6}

    BLINK_MIN = 0.08
    BLINK_RANGE = 0.77
    BLINK_SPEED = 1.5
    GHOST_BLEND = 0.22
    GHOST_SCALE = 0.88
    VANISH_BLEND = 0.25

    def __init__(self, canvas: tk.Canvas, palette: Palette, vanish_steps: int = DEFAULT_VANISH_STEPS) -> None:
        self._canvas = canvas
        self._palette = palette
        self._vanish_steps = vanish_steps

    def render(self, game: InfiniteTicTacToeLogic, metrics: BoardMetrics, state: BoardViewState) -> None:
        self._canvas.delete("all")
        expiring = None if game.game_over else game.get_expiring_piece()

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self._draw_cell(game, metrics, state, (r, c), expiring)

        self._draw_winning_strike(game, metrics, state)
        self._draw_confetti(state)

    # -- cells ---------------------------------------------------------------

    def _draw_cell(
        self,
        game: InfiniteTicTacToeLogic,
        metrics: BoardMetrics,
        state: BoardViewState,
        cell: Cell,
        expiring: Optional[Cell],
    ) -> None:
        p = self._palette
        r, c = cell
        x0, y0, x1, y1 = metrics.cell_rect(r, c)
        cx, cy = metrics.cell_center(r, c)

        is_empty = game.board[r][c] is None
        is_hovered = is_empty and not game.game_over and state.hovered == cell

        draw_rounded_rect(
            self._canvas, x0, y0, x1, y1, radius=metrics.cell_radius,
            fill=p.cell_hover if is_hovered else p.cell, outline=p.grid_line, width=1,
        )

        if state.vanish and state.vanish.cell == cell:
            self._draw_vanishing(metrics, state.vanish, cx, cy)

        piece = game.get_piece_info(r, c)
        if piece:
            self._draw_piece(metrics, piece, (x1, y1), (cx, cy), expiring == cell, state.pulse_phase)
        elif is_hovered:
            self._draw_ghost(game.current_player, metrics, cx, cy)

    def _draw_mark(
        self,
        player: str,
        metrics: BoardMetrics,
        cx: float,
        cy: float,
        color: str,
        width: int,
        scale: float = 1.0,
    ) -> None:
        if player == "X":
            draw_x(self._canvas, cx, cy, metrics.mark_half * scale, color, width)
        else:
            draw_o(self._canvas, cx, cy, metrics.mark_radius * scale, color, width)

    def _draw_piece(
        self,
        metrics: BoardMetrics,
        piece: Dict[str, Any],
        corner: Tuple[int, int],
        center: Tuple[float, float],
        is_expiring: bool,
        pulse_phase: float,
    ) -> None:
        p = self._palette
        player, age = piece["player"], piece["age"]
        base_color = p.mark_color(player)
        fade = self.FADE_BY_AGE.get(age, 1.0)

        if is_expiring:  # only the mark blinks, the pips keep their normal colour
            blink = (math.sin(pulse_phase * self.BLINK_SPEED) + 1.0) / 2.0
            mark_fade = self.BLINK_MIN + self.BLINK_RANGE * blink
        else:
            mark_fade = fade

        mark_color = blend_hex_colors(p.cell, base_color, mark_fade)
        pip_color = blend_hex_colors(p.cell, base_color, fade)
        width = max(2, int(metrics.mark_stroke * self.STROKE_BY_AGE.get(age, 0.8)))

        self._draw_mark(player, metrics, *center, mark_color, width)
        self._draw_pips(metrics, corner, age, pip_color)

    def _draw_pips(self, metrics: BoardMetrics, corner: Tuple[int, int], count: int, color: str) -> None:
        right = corner[0] - metrics.cell_radius * 0.7
        bottom = corner[1] - metrics.cell_radius * 0.8
        radius = metrics.pip_radius
        for i in range(count):
            px = right - (count - 1 - i) * metrics.pip_spacing
            self._canvas.create_oval(px - radius, bottom - radius, px + radius, bottom + radius, fill=color, outline="")

    def _draw_ghost(self, player: str, metrics: BoardMetrics, cx: float, cy: float) -> None:
        p = self._palette
        color = blend_hex_colors(p.cell_hover, p.mark_color(player), self.GHOST_BLEND)
        width = max(2, int(metrics.mark_stroke * 0.55))
        self._draw_mark(player, metrics, cx, cy, color, width, scale=self.GHOST_SCALE)

    def _draw_vanishing(self, metrics: BoardMetrics, effect: VanishEffect, cx: float, cy: float) -> None:
        p = self._palette
        ratio = effect.step / self._vanish_steps
        color = blend_hex_colors(p.cell, p.mark_color(effect.player), ratio * self.VANISH_BLEND)
        width = max(1, int(metrics.mark_stroke * 0.5 * ratio))
        self._draw_mark(effect.player, metrics, cx, cy, color, width, scale=ratio)

    # -- overlays ------------------------------------------------------------

    def _draw_winning_strike(
        self, game: InfiniteTicTacToeLogic, metrics: BoardMetrics, state: BoardViewState,
    ) -> None:
        line = game.winning_line
        if not (line and game.winner and len(line) >= GRID_SIZE):
            return

        cx0, cy0 = metrics.cell_center(*line[0])
        cx2, cy2 = metrics.cell_center(*line[-1])
        dx, dy = cx2 - cx0, cy2 - cy0
        dist = math.hypot(dx, dy)
        if dist == 0:
            return

        ux, uy = dx / dist, dy / dist
        ext = metrics.strike_extend
        sx, sy = cx0 - ux * ext, cy0 - uy * ext
        ex, ey = cx2 + ux * ext, cy2 + uy * ext
        t = state.win_progress

        self._canvas.create_line(
            sx, sy, sx + (ex - sx) * t, sy + (ey - sy) * t,
            fill=self._palette.strike_color(game.winner),
            width=metrics.strike_width,
            capstyle=tk.BUTT,
        )

    def _draw_confetti(self, state: BoardViewState) -> None:
        for p in state.confetti:
            if p.shape == "rect":
                self._canvas.create_rectangle(p.x, p.y, p.x + p.size, p.y + p.size * 0.6, fill=p.color, outline="")
            else:
                self._canvas.create_oval(p.x, p.y, p.x + p.size, p.y + p.size, fill=p.color, outline="")
