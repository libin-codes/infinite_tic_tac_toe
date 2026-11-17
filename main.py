#!/usr/bin/env python3
"""Launch script for Infinite Tic-Tac-Toe."""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from infinite_tic_tac_toe import main

if __name__ == "__main__":
    main()
