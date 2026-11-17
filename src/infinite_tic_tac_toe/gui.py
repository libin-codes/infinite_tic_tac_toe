"""Responsive Tkinter GUI for Infinite Tic-Tac-Toe.

Structure (top to bottom):

    1. Theme            Palette, FontBook, ButtonStyle presets
    2. Drawing helpers  colour blending, rounded rectangles, X / O marks
    3. Board model      BoardMetrics (all geometry derived from ONE number),
                        BoardViewState, ConfettiParticle
    4. Widgets          RoundedButton, PlayerCard, RoundBanner, RulesDialog
    5. Composite views  Sidebar, BoardRenderer, BoardView
    6. Application      InfiniteTicTacToeApp (wires game logic <-> UI)

Sizing philosophy: nothing is positioned with a fixed pixel size.
  * Panes use grid weights, children use ``place`` with relative coordinates.
  * The board derives every dimension from a single side length.
  * Fonts are named ``tkinter.font.Font`` objects rescaled from the window size.
  * Component paddings derive from the component's own height / font height.
"""

from __future__ import annotations

import math
import random
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass, field
from tkinter import messagebox
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from infinite_tic_tac_toe.logic import InfiniteTicTacToeLogic

Cell = Tuple[int, int]

GRID_SIZE = 3
DEFAULT_WINDOW = (1400, 900)  # also the reference size used for font scaling
MIN_WINDOW = (1050, 650)


# =============================================================================
# 1. THEME
# =============================================================================


@dataclass(frozen=True)
class Palette:
    """All colours used by the UI."""

    bg: str = "#13141f"
    sidebar: str = "#181926"
    surface: str = "#1e1f2e"
    surface_light: str = "#282a3d"
    surface_light_hover: str = "#383a54"
    divider: str = "#26273b"

    card_active: str = "#25273b"
    card_inactive: str = "#191a27"
    card_border: str = "#2d2f44"

    cell: str = "#242538"
    cell_hover: str = "#2f314c"
    grid_line: str = "#383952"

    text: str = "#e2e8f0"
    text_muted: str = "#94a3b8"
    text_dim: str = "#64748b"

    accent: str = "#2563eb"
    accent_hover: str = "#1d4ed8"

    x: str = "#38bdf8"
    o: str = "#f43f5e"
    x_strike: str = "#0284c7"
    o_strike: str = "#e11d48"
    x_avatar: str = "#0c4a6e"
    o_avatar: str = "#3d0c18"

    confetti: Tuple[str, ...] = (
        "#38bdf8", "#f43f5e", "#fbbf24", "#34d399",
        "#a78bfa", "#f472b6", "#60a5fa", "#fde047",
    )

    def mark_color(self, player: str) -> str:
        return self.x if player == "X" else self.o

    def strike_color(self, player: str) -> str:
        return self.x_strike if player == "X" else self.o_strike

    def avatar_bg(self, player: str) -> str:
        return self.x_avatar if player == "X" else self.o_avatar


PALETTE = Palette()


class FontBook:
    """Named fonts that are rescaled together when the window size changes."""

    FAMILY = "Helvetica"
    MIN_SIZE = 7
    SPECS: Dict[str, Tuple[int, Literal["normal", "bold"]]] = {
        "eyebrow": (12, "bold"),
        "title": (17, "bold"),
        "section": (10, "bold"),
        "player_name": (12, "bold"),
        "status_active": (9, "bold"),
        "status_idle": (9, "normal"),
        "badge": (20, "bold"),
        "avatar": (24, "bold"),
        "button_primary": (11, "bold"),
        "button_secondary": (10, "bold"),
        "button_muted": (10, "normal"),
        "round": (18, "bold"),
        "dialog_title": (14, "bold"),
        "dialog_heading": (10, "bold"),
        "dialog_body": (9, "normal"),
    }

    def __init__(self, root: tk.Misc) -> None:
        self._fonts: Dict[str, tkfont.Font] = {
            name: tkfont.Font(root=root, family=self.FAMILY, size=size, weight=weight)
            for name, (size, weight) in self.SPECS.items()
        }

    def __getitem__(self, name: str) -> tkfont.Font:
        return self._fonts[name]

    def rescale(self, factor: float) -> None:
        for name, (base_size, _) in self.SPECS.items():
            self._fonts[name].configure(size=max(self.MIN_SIZE, round(base_size * factor)))

    def line_height(self, name: str) -> int:
        return int(self._fonts[name].metrics("linespace"))


@dataclass(frozen=True)
class ButtonStyle:
    bg: str
    hover: str
    fg: str
    font: str  # name inside FontBook
    disabled_bg: Optional[str] = None
    disabled_fg: Optional[str] = None


def build_button_styles(p: Palette) -> Dict[str, ButtonStyle]:
    return {
        "primary": ButtonStyle(
            p.accent,
            p.accent_hover,
            "white",
            "button_primary",
            disabled_bg="#1d2238",
            disabled_fg="#4b5563",
        ),
        "secondary": ButtonStyle(
            p.surface_light,
            p.surface_light_hover,
            p.text,
            "button_secondary",
            disabled_bg=p.surface,
            disabled_fg="#4b5563",
        ),
        "muted": ButtonStyle(
            p.surface_light,
            p.surface_light_hover,
            p.text_muted,
            "button_muted",
            disabled_bg=p.surface,
            disabled_fg="#4b5563",
        ),
    }


# =============================================================================
# 2. DRAWING HELPERS
# =============================================================================


def blend_hex_colors(c1: str, c2: str, t: float) -> str:
    """Blend two hex colours. t=0.0 yields c1, t=1.0 yields c2."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    **kwargs: Any,
) -> int:
    """Draw a smooth rounded rectangle on a Tkinter Canvas."""
    radius = max(0.0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius, y1, x1 + radius, y1,
        x2 - radius, y1, x2 - radius, y1,
        x2, y1, x2, y1 + radius,
        x2, y1 + radius, x2, y2 - radius,
        x2, y2 - radius, x2, y2,
        x2 - radius, y2, x2 - radius, y2,
        x1 + radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius,
        x1, y2 - radius, x1, y1 + radius,
        x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def draw_x(canvas: tk.Canvas, cx: float, cy: float, half: float, color: str, width: int) -> None:
    for sign in (1, -1):
        canvas.create_line(
            cx - half * sign, cy - half, cx + half * sign, cy + half,
            fill=color, width=width, capstyle=tk.ROUND,
        )


def draw_o(canvas: tk.Canvas, cx: float, cy: float, radius: float, color: str, width: int) -> None:
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=color, width=width)


# =============================================================================
# 3. BOARD MODEL
# =============================================================================


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


# =============================================================================
# 4. WIDGETS
# =============================================================================


class RoundedButton(tk.Canvas):
    """Canvas button with smooth rounded corners and a hover effect.

    Corner radius is a fraction of the button's own height, so the button
    looks the same at any size. Size it with ``place``/``pack(fill=...)``.
    """

    RADIUS_RATIO = 0.28

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command: Optional[Callable[[], None]],
        style: ButtonStyle,
        fonts: FontBook,
        parent_bg: str,
        height: Optional[int] = None,
        width: Optional[int] = None,
    ) -> None:
        options: Dict[str, Any] = {"highlightthickness": 0, "cursor": "hand2", "bg": parent_bg}
        if height:
            options["height"] = height
        if width:
            options["width"] = width
        super().__init__(parent, **options)

        self._text = text
        self._command = command
        self._style = style
        self._fonts = fonts
        self._current_bg = style.bg
        self._enabled = True

        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", lambda e: self._on_click())

    def _on_click(self) -> None:
        if self._enabled and self._command:
            self._command()

    def _set_hover(self, hovering: bool) -> None:
        if not self._enabled:
            return
        self._current_bg = self._style.hover if hovering else self._style.bg
        self.redraw()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        if self._enabled == enabled:
            return
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "")
        self._current_bg = self._style.bg if enabled else (self._style.disabled_bg or self._style.bg)
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 2 or h <= 2:
            return
        bg = self._current_bg if self._enabled else (self._style.disabled_bg or self._style.bg)
        fg = self._style.fg if self._enabled else (self._style.disabled_fg or self._style.fg)
        draw_rounded_rect(self, 1, 1, w - 1, h - 1, radius=h * self.RADIUS_RATIO, fill=bg, outline="")
        self.create_text(w / 2, h / 2, text=self._text, fill=fg, font=self._fonts[self._style.font])


class PlayerCard(tk.Frame):
    """Sidebar card: square avatar with mark X/O, name + status, and bold wins on the right."""

    GAP_RATIO = 0.14  # inner gap as a fraction of the card height

    def __init__(self, parent: tk.Misc, mark: str, palette: Palette, fonts: FontBook) -> None:
        super().__init__(
            parent,
            bg=palette.card_inactive,
            highlightbackground=palette.card_border,
            highlightthickness=1,
        )
        self._mark = mark
        self._palette = palette
        self._fonts = fonts
        accent = palette.mark_color(mark)

        self._avatar = tk.Frame(self, bg=palette.avatar_bg(mark))
        self._avatar_label = tk.Label(
            self._avatar, text=mark, font=fonts["avatar"], bg=palette.avatar_bg(mark), fg=accent,
        )
        self._avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        self._info = tk.Frame(self, bg=palette.card_inactive)
        self._name = tk.Label(self._info, text=f"Player {mark}", font=fonts["player_name"], anchor="w")
        self._name.pack(anchor="w", pady=(0, 4))
        self._status = tk.Label(self._info, anchor="w")
        self._status.pack(anchor="w")

        self._wins = tk.Label(self, text="0", font=fonts["badge"])

        self._avatar.place(x=0, y=0, relheight=1, width=1)
        self._info.place(rely=0.5, anchor="w")
        self._wins.place(relx=1.0, rely=0.5, anchor="e")
        self.bind("<Configure>", self._layout)

        self.apply(active=False, wins=0, status="WAITING")

    def _layout(self, event: tk.Event) -> None:
        """Keep the avatar square and derive paddings from the card height."""
        height = event.height
        gap = int(height * self.GAP_RATIO)
        self._avatar.place_configure(width=height)
        self._info.place_configure(x=height + gap)
        self._wins.place_configure(x=-gap * 1.5)

    def apply(self, active: bool, wins: int, status: str) -> None:
        p = self._palette
        accent = p.mark_color(self._mark)
        bg = p.card_active if active else p.card_inactive

        self.configure(
            bg=bg,
            highlightbackground=accent if active else p.card_border,
            highlightthickness=2 if active else 1,
        )
        self._info.configure(bg=bg)
        self._name.configure(bg=bg, fg=p.text if active else p.text_muted)
        self._status.configure(
            bg=bg,
            fg=accent if active else p.text_dim,
            font=self._fonts["status_active" if active else "status_idle"],
            text=status,
        )
        self._wins.configure(bg=bg, text=str(wins), fg=p.text)


class RoundBanner(tk.Label):
    """Header text that shows the round / winner with no background or border."""

    def __init__(self, parent: tk.Misc, palette: Palette, fonts: FontBook) -> None:
        super().__init__(
            parent,
            bg=palette.bg,
            fg=palette.text,
            font=fonts["round"],
            highlightthickness=0,
        )
        self._palette = palette
        self._fonts = fonts

    def set(self, text: str, color: Optional[str] = None) -> None:
        self.configure(text=text, fg=color or self._palette.text)

    def redraw(self) -> None:
        self.configure(font=self._fonts["round"])


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


# =============================================================================
# 5. COMPOSITE VIEWS
# =============================================================================


@dataclass(frozen=True)
class ButtonSpec:
    label: str
    style: str  # key into build_button_styles()
    action: str  # attribute name on SidebarActions


@dataclass(frozen=True)
class SidebarActions:
    new_round: Callable[[], None]
    reset_scores: Callable[[], None]
    show_rules: Callable[[], None]
    toggle_fullscreen: Callable[[], None]


class Sidebar(tk.Frame):
    """Left panel: title, player cards and action buttons.

    Every vertical position is a fraction of the sidebar's height, so the
    layout stretches with the window.
    """

    # Layout (fractions of sidebar width / height)
    SIDE_MARGIN = 0.06
    HEADER_HEIGHT = 0.12
    PLAYERS_LABEL_Y = 0.155
    CARD_TOP = 0.19
    CARD_HEIGHT = 0.10
    CARD_STEP = 0.12
    BUTTONS_TOP = 0.75
    BUTTON_HEIGHT = 0.07
    BUTTON_STEP = 0.080

    BUTTON_SPECS: Tuple[ButtonSpec, ...] = (
        ButtonSpec("🔄 New Round (R)", "primary", "new_round"),
        ButtonSpec("↺ Reset Scores", "secondary", "reset_scores"),
        ButtonSpec("❓ How to Play", "secondary", "show_rules"),
       
    )

    def __init__(
        self,
        parent: tk.Misc,
        palette: Palette,
        fonts: FontBook,
        styles: Dict[str, ButtonStyle],
        actions: SidebarActions,
    ) -> None:
        super().__init__(parent, bg=palette.sidebar)
        self._palette = palette
        self._fonts = fonts
        self._styles = styles
        self._actions = actions

        self.cards: Dict[str, PlayerCard] = {}
        self.buttons: Dict[str, RoundedButton] = {}
        self._buttons: List[RoundedButton] = []

        self._build_header()
        self._build_players_section()
        self._build_cards()
        self._build_buttons()

    # -- construction --------------------------------------------------------

    def _build_header(self) -> None:
        p, m = self._palette, self.SIDE_MARGIN
        tk.Label(
            self, text="INFINITE", font=self._fonts["eyebrow"], bg=p.sidebar, fg=p.x,
        ).place(relx=m, rely=self.HEADER_HEIGHT * 0.36, anchor="w")
        tk.Label(
            self, text="TIC-TAC-TOE", font=self._fonts["title"], bg=p.sidebar, fg=p.text,
        ).place(relx=m, rely=self.HEADER_HEIGHT * 0.70, anchor="w")
        tk.Frame(self, bg=p.divider).place(relx=0, rely=self.HEADER_HEIGHT, relwidth=1, height=1)

    def _build_players_section(self) -> None:
        p, m = self._palette, self.SIDE_MARGIN
        tk.Label(
            self, text="PLAYERS", font=self._fonts["section"], bg=p.sidebar, fg=p.text_dim,
        ).place(relx=m, rely=self.PLAYERS_LABEL_Y, anchor="w")

    def _build_cards(self) -> None:
        for index, mark in enumerate(("X", "O")):
            card = PlayerCard(self, mark, self._palette, self._fonts)
            card.place(
                relx=self.SIDE_MARGIN,
                rely=self.CARD_TOP + index * self.CARD_STEP,
                relwidth=1 - 2 * self.SIDE_MARGIN,
                relheight=self.CARD_HEIGHT,
            )
            self.cards[mark] = card

    def _build_buttons(self) -> None:
        for index, spec in enumerate(self.BUTTON_SPECS):
            button = RoundedButton(
                self,
                spec.label,
                getattr(self._actions, spec.action),
                self._styles[spec.style],
                self._fonts,
                parent_bg=self._palette.sidebar,
            )
            button.place(
                relx=self.SIDE_MARGIN,
                rely=self.BUTTONS_TOP + index * self.BUTTON_STEP,
                relwidth=1 - 2 * self.SIDE_MARGIN,
                relheight=self.BUTTON_HEIGHT,
            )
            self._buttons.append(button)
            self.buttons[spec.action] = button

    # -- public API ----------------------------------------------------------

    def set_button_enabled(self, action: str, enabled: bool) -> None:
        if action in self.buttons:
            self.buttons[action].set_enabled(enabled)

    def update_players(self, game: InfiniteTicTacToeLogic, scores: Dict[str, int]) -> None:
        for mark, card in self.cards.items():
            if game.game_over:
                active = game.winner == mark
                status = "🏆 WINNER" if active else "DEFEAT"
            else:
                active = game.current_player == mark
                status = "TURN" if active else "WAITING"
            card.apply(active=active, wins=scores[mark], status=status)

    def redraw_buttons(self) -> None:
        for button in self._buttons:
            button.redraw()


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

    def __init__(self, canvas: tk.Canvas, palette: Palette) -> None:
        self._canvas = canvas
        self._palette = palette

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
        ratio = effect.step / BoardView.VANISH_STEPS
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
        self._renderer = BoardRenderer(self.canvas, palette)

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


# =============================================================================
# 6. APPLICATION
# =============================================================================


class InfiniteTicTacToeApp:
    """Main window: owns the game and scores and wires them to the views."""

    # Pane proportions (grid weights): sidebar 2 : board area 5  (~29% / 71%)
    SIDEBAR_WEIGHT = 2
    MAIN_WEIGHT = 5

    # Floating round banner: distance from the top as a fraction of window height
    BANNER_TOP = 0.04

    # Font scaling
    MIN_SCALE = 0.7
    MAX_SCALE = 1.2
    SCALE_EPSILON = 0.02

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.palette = PALETTE
        self.game = InfiniteTicTacToeLogic()
        self.scores: Dict[str, int] = {"X": 0, "O": 0}
        self.round_number = 1
        self.is_fullscreen = False
        self._scale = 1.0

        self._configure_window()
        self.fonts = FontBook(root)
        self.styles = build_button_styles(self.palette)

        self._build_layout()
        self._bind_events()
        self._refresh_all()

    # -- window --------------------------------------------------------------

    def _configure_window(self) -> None:
        self.root.title("Infinite Tic-Tac-Toe")
        self.root.geometry(f"{DEFAULT_WINDOW[0]}x{DEFAULT_WINDOW[1]}")
        self.root.minsize(*MIN_WINDOW)
        self.root.configure(bg=self.palette.bg)

        try:
            self.root.attributes("-zoomed", True)  # Linux
        except tk.TclError:
            try:
                self.root.state("zoomed")  # Windows
            except tk.TclError:
                sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                self.root.geometry(f"{sw}x{sh}+0+0")

    def _toggle_fullscreen(self, event: Optional[tk.Event] = None) -> None:
        self._set_fullscreen(not self.is_fullscreen)

    def _exit_fullscreen(self, event: Optional[tk.Event] = None) -> None:
        if self.is_fullscreen:
            self._set_fullscreen(False)

    def _set_fullscreen(self, enabled: bool) -> None:
        self.is_fullscreen = enabled
        try:
            self.root.attributes("-fullscreen", enabled)
        except tk.TclError:
            pass

    # -- layout --------------------------------------------------------------

    def _build_layout(self) -> None:
        root = self.root
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=self.SIDEBAR_WEIGHT, uniform="panes")
        root.grid_columnconfigure(1, weight=0)
        root.grid_columnconfigure(2, weight=self.MAIN_WEIGHT, uniform="panes")

        self.sidebar = Sidebar(
            root, self.palette, self.fonts, self.styles,
            SidebarActions(
                new_round=self.on_new_round,
                reset_scores=self.on_reset_all,
                show_rules=self.show_rules,
                toggle_fullscreen=self._toggle_fullscreen,
            ),
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        tk.Frame(root, bg=self.palette.divider, width=1).grid(row=0, column=1, sticky="ns")

        self.main_area = tk.Frame(root, bg=self.palette.bg)
        self.main_area.grid(row=0, column=2, sticky="nsew")

        self.board_view = BoardView(self.main_area, self.game, self.palette, self._handle_cell_click)
        self.board_view.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Created after the board so it floats above it.
        self.banner = RoundBanner(self.main_area, self.palette, self.fonts)
        self.banner.place(relx=0.5, rely=self.BANNER_TOP, anchor="n")

    def _bind_events(self) -> None:
        self.root.bind("<r>", lambda e: self.on_new_round())
        self.root.bind("<R>", lambda e: self.on_new_round())
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)
        self.root.bind("<Configure>", self._on_root_configure)

    def _on_root_configure(self, event: tk.Event) -> None:
        """Rescale all fonts proportionally to the window size."""
        if event.widget is not self.root:
            return
        factor = min(event.width / DEFAULT_WINDOW[0], event.height / DEFAULT_WINDOW[1])
        factor = max(self.MIN_SCALE, min(self.MAX_SCALE, factor))
        if abs(factor - self._scale) < self.SCALE_EPSILON:
            return

        self._scale = factor
        self.fonts.rescale(factor)
        self.sidebar.redraw_buttons()
        self.banner.redraw()

    # -- view updates --------------------------------------------------------

    def _refresh_all(self) -> None:
        self.sidebar.update_players(self.game, self.scores)
        self.sidebar.set_button_enabled("new_round", not self.game.is_empty)
        self._show_round()
        self.board_view.render()

    def _show_round(self) -> None:
        self.banner.set(f"ROUND {self.round_number}")

    def _show_winner(self, winner: str) -> None:
        self.banner.set(f"PLAYER {winner} WINS ROUND {self.round_number}!")

    # -- game flow -----------------------------------------------------------

    def _handle_cell_click(self, r: int, c: int) -> None:
        if not self.game.is_valid_move(r, c):
            return

        result = self.game.make_move(r, c)
        if not result["success"]:
            return

        if result["vanished"]:
            self.board_view.play_vanish(tuple(result["vanished"]), result["player"])

        if result["game_over"]:
            winner = result["winner"]
            self.scores[winner] += 1
            self.sidebar.update_players(self.game, self.scores)
            self._show_winner(winner)
            self.board_view.play_win()
        else:
            self.sidebar.update_players(self.game, self.scores)
            self._show_round()
        self.sidebar.set_button_enabled("new_round", not self.game.is_empty)
        self.board_view.render()

    def on_new_round(self) -> None:
        if self.game.is_empty:
            return

        if not self.game.game_over:
            if not messagebox.askyesno(
                "New Round",
                "A game is currently in progress. Are you sure you want to start a new round?",
                parent=self.root,
            ):
                return

        self.round_number += 1
        self.game.reset(alternate_starting=True)
        self.board_view.clear_effects()
        self._refresh_all()

    def on_reset_all(self) -> None:
        has_progress = self.round_number > 1 or any(self.scores.values())
        if has_progress and not messagebox.askyesno(
            "Reset Scores",
            "Are you sure you want to reset all scores and start over?",
            parent=self.root,
        ):
            return

        self.scores = {"X": 0, "O": 0}
        self.round_number = 1
        self.game.reset(alternate_starting=False)
        self.board_view.clear_effects()
        self._refresh_all()

    def show_rules(self) -> None:
        RulesDialog(self.root, self.palette, self.fonts, self.styles)


def main() -> None:
    root = tk.Tk()
    InfiniteTicTacToeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()