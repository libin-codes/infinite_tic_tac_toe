"""Transient visual states and animation particle models for the board."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from infinite_tic_tac_toe.models.game import Cell


class ConfettiParticle:
    """Particle for the victory celebration. ``unit`` scales motion with board size."""

    def __init__(self, x: float, y: float, bounds_height: float, unit: float, colors: Tuple[str, ...]) -> None:
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5) * unit
        self.vy = random.uniform(-10, -3) * unit
        self.gravity = random.uniform(0.3, 0.6) * unit
        self.size = random.uniform(6, 12) * unit
        self.color = random.choice(colors)
        self.shape = random.choice(("rect", "oval"))
        self.life = 1.0
        self.decay = random.uniform(0.012, 0.024)
        self._floor = bounds_height + 30 * unit

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= self.decay
        return self.life > 0 and self.y < self._floor


@dataclass
class VanishEffect:
    cell: Cell
    player: str
    step: int


@dataclass
class BoardViewState:
    """Transient visual state, separate from the game rules."""

    hovered: Optional[Cell] = None
    pulse_phase: float = 0.0
    vanish: Optional[VanishEffect] = None
    win_progress: float = 1.0
    confetti: List[ConfettiParticle] = field(default_factory=list)
