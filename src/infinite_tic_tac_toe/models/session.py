"""Match session and score tracking model."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class GameSession:
    """Tracks scores across rounds and match progression."""

    round_number: int = 1
    scores: Dict[str, int] = field(default_factory=lambda: {"X": 0, "O": 0})

    def record_win(self, winner: str) -> None:
        """Increment win count for the winning player."""
        if winner in self.scores:
            self.scores[winner] += 1

    def next_round(self) -> int:
        """Advance to the next round."""
        self.round_number += 1
        return self.round_number

    def reset_all(self) -> None:
        """Reset scores and round count to initial state."""
        self.scores = {"X": 0, "O": 0}
        self.round_number = 1

    @property
    def has_progress(self) -> bool:
        """Return True if rounds have been played or any player has points."""
        return self.round_number > 1 or any(self.scores.values())
