"""Infinite Tic-Tac-Toe package."""

import sys
from pathlib import Path

# Ensure src directory is in sys.path when executed directly
_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from infinite_tic_tac_toe.controllers import GameController, InfiniteTicTacToeApp
from infinite_tic_tac_toe.models import GameSession, InfiniteTicTacToeLogic


def main() -> None:
    """Launch the Infinite Tic-Tac-Toe application."""
    import tkinter as tk
    root = tk.Tk()
    GameController(root)
    root.mainloop()


__all__ = [
    "GameController",
    "InfiniteTicTacToeApp",
    "InfiniteTicTacToeLogic",
    "GameSession",
    "main",
]


if __name__ == "__main__":
    main()
