# Infinite Tic-Tac-Toe (Python Tkinter)

A modern, fluid desktop implementation of **Infinite Tic-Tac-Toe** built with Python and Tkinter.

Unlike traditional Tic-Tac-Toe which frequently ends in boring stalemates/draws, Infinite Tic-Tac-Toe keeps the game dynamic: **each player can only keep at most 3 marks on the board at any time**. When a player places their 4th mark, their oldest mark automatically fades away and vanishes!

---

## 🎮 How to Play & Rules

1. **Move Limit**: Each player ('X' and 'O') may have a maximum of **3 pieces** on the 3×3 grid.
2. **The Fading Queue**:
   - **Move 1, 2, and 3**: Marks are placed normally.
   - **Move 4+**: Placing a new mark automatically causes that player's **oldest mark to fade away and disappear**.
3. **Visual Age & Pip Indicators**:
   - `● ● ●` **(3 pips)**: Newest mark (brightest, thickest neon color).
   - `● ●` **(2 pips)**: Middle mark (standard color).
   - `●` **(1 pip)**: Oldest mark (faded color).
4. **Warning Blink**: When it's your turn and you already have 3 marks on the board, your oldest mark smoothly blinks to signal that it will vanish on your next move.
5. **Winning**: Align 3 of your marks horizontally, vertically, or diagonally to win the round! Ties are impossible because pieces continuously rotate.

---

## ✨ Features

- **Two-Column Gaming Layout**:
  - **Left Sidebar**: Displays title header, player roster with square X/O avatars, live turn status, and bold win counters on the right, plus action buttons at the bottom.
  - **Right Main Area**: Features a game status header bar and a centered board that dynamically scales to fill any display.
- **Full Screen & Responsive Scaling**: Automatically launches maximized (`root.attributes('-zoomed', True)`), dynamically recalculating board canvas, cell sizes, line thicknesses, strike extensions, and pip radiuses to fill your screen with comfortable margins. Toggle borderless fullscreen anytime with `F11`.
- **Smooth Fading & Animations**:
  - Color blending representing the age of each piece.
  - Dissolve animation when an expired mark disappears.
  - Smooth rhythmic blinking on the mark that will expire on the current turn.
  - Animated gold strike-through line connecting the winning 3-in-a-row marks.
  - Confetti particle explosion celebrating the winner.
  - Ghost hover indicator previewing moves before clicking.
- **Scoreboard & Round Tracking**: Tracks wins across rounds and alternates who goes first each round.
- **Rules Modal**: In-game rules guide accessible with one click.
- **Keyboard Shortcuts**: Press `R` to quickly start a new round.
- **Zero External Dependencies**: Pure Python standard library (`tkinter`), requiring no third-party package installation.

---

## 🚀 Running the Game

You can run the game using either standard Python or `uv`:

```bash
# Direct run
python3 main.py
```

Or as a module:

```bash
python3 -m infinite_tic_tac_toe
```

Or using `uv`:

```bash
uv run infinite-tic-tac-toe
```

---

## 🧪 Running Tests

A suite of unit and GUI tests is included:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
