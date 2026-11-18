"""Board geometry metrics derived from a single target side length."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from infinite_tic_tac_toe.models.game import Cell
from infinite_tic_tac_toe.views.theme import GRID_SIZE


@dataclass(frozen=True)
class BoardMetrics:
    """Every board dimension, derived from one target side length."""

    margin: int
    gap: int
    cell: int
    cell_radius: int
    mark_half: int
    mark_radius: int
    mark_stroke: int
    strike_extend: int
    strike_width: int
    pip_radius: float
    pip_spacing: float

    @classmethod
    def for_side(cls, side: int) -> "BoardMetrics":
        margin = int(side * 0.045)
        gap = int(side * 0.035)
        cell = (side - 2 * margin - 2 * gap) // GRID_SIZE
        return cls(
            margin=margin,
            gap=gap,
            cell=cell,
            cell_radius=max(1, int(cell * 0.12)),
            mark_half=int(cell * 0.28),
            mark_radius=int(cell * 0.30),
            mark_stroke=max(2, int(cell * 0.075)),
            strike_extend=int(cell * 0.44),
            strike_width=max(2, int(cell * 0.085)),
            pip_radius=max(1.0, cell * 0.024),
            pip_spacing=max(2.0, cell * 0.060),
        )

    @property
    def size(self) -> int:
        """Total canvas side length."""
        return 2 * self.margin + (GRID_SIZE - 1) * self.gap + GRID_SIZE * self.cell

    def cell_rect(self, r: int, c: int) -> Tuple[int, int, int, int]:
        x0 = self.margin + c * (self.cell + self.gap)
        y0 = self.margin + r * (self.cell + self.gap)
        return x0, y0, x0 + self.cell, y0 + self.cell

    def cell_center(self, r: int, c: int) -> Tuple[float, float]:
        x0, y0, x1, y1 = self.cell_rect(r, c)
        return (x0 + x1) / 2, (y0 + y1) / 2

    def cell_at(self, x: int, y: int) -> Optional[Cell]:
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x0, y0, x1, y1 = self.cell_rect(r, c)
                if x0 <= x <= x1 and y0 <= y <= y1:
                    return r, c
        return None
