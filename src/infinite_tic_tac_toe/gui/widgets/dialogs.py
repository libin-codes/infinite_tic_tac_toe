"""Modal dialogs including the 'How to Play' rules window."""

from __future__ import annotations

import tkinter as tk
from typing import Dict, Tuple

from infinite_tic_tac_toe.gui.theme import ButtonStyle, FontBook, Palette
from infinite_tic_tac_toe.gui.widgets.button import RoundedButton

RULES: Tuple[Tuple[str, str], ...] = (
    ("1. Max 3 Marks Per Player", "Each player can only maintain up to 3 marks simultaneously on the 3x3 board."),
    ("2. The Fading Queue", "When you have 3 marks and place a 4th, your OLDEST mark fades away and vanishes forever!"),
    ("3. Visual Pip Indicators", "Look at the dots in the corner of each cell:\n   ●     = Oldest (Will vanish next!)\n   ● ●   = 2nd Mark\n   ● ● ● = Newest (Just placed)"),
    ("4. Warning Blink", "When it is your turn and you already have 3 marks, your oldest mark blinks smoothly to show that it will vanish next."),
    ("5. Winning", "Align 3 of your marks in a row (horizontal, vertical, or diagonal) to win the round! Ties are impossible because pieces keep recycling."),
)


class RulesDialog(tk.Toplevel):
    """Modal 'How to Play' window. Sized by its content and centred over the parent."""

    WRAP_RATIO = 0.30  # text wrap width as a fraction of the parent window width

    def __init__(self, parent: tk.Tk, palette: Palette, fonts: FontBook, styles: Dict[str, ButtonStyle]) -> None:
        super().__init__(parent)
        self.title("How to Play: Infinite Tic-Tac-Toe")
        self.resizable(False, False)
        self.configure(bg=palette.bg)
        self.transient(parent)

        line = fonts.line_height("dialog_body")
        wrap = int(parent.winfo_width() * self.WRAP_RATIO)

        content = tk.Frame(self, bg=palette.bg, padx=line * 2, pady=int(line * 1.5))
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content, text="Infinite Tic-Tac-Toe Rules",
            font=fonts["dialog_title"], bg=palette.bg, fg=palette.text,
        ).pack(pady=(0, line))

        for heading, body in RULES:
            self._add_rule(content, heading, body, palette, fonts, wrap, line)

        RoundedButton(
            content, "Got it!", self.destroy, styles["primary"], fonts, palette.bg,
            height=int(line * 2.6), width=int(line * 9),
        ).pack(pady=(line, 0))

        self._center_over(parent)
        self.wait_visibility()
        self.grab_set()

    @staticmethod
    def _add_rule(
        parent: tk.Misc, heading: str, body: str,
        palette: Palette, fonts: FontBook, wrap: int, line: int,
    ) -> None:
        item = tk.Frame(parent, bg=palette.bg)
        item.pack(fill=tk.X, pady=(0, line // 2))
        tk.Label(
            item, text=heading, font=fonts["dialog_heading"],
            bg=palette.bg, fg=palette.x, anchor="w",
        ).pack(fill=tk.X)
        tk.Label(
            item, text=body, font=fonts["dialog_body"], bg=palette.bg, fg=palette.text_muted,
            justify=tk.LEFT, anchor="w", wraplength=wrap,
        ).pack(fill=tk.X, padx=(line // 2, 0))

    def _center_over(self, parent: tk.Tk) -> None:
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
