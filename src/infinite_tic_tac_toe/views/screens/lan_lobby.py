"""LAN Lobby screen with two-column split layout for hosting and joining games."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, Optional

from infinite_tic_tac_toe.network.discovery import generate_room_code
from infinite_tic_tac_toe.views.components.button import RoundedButton
from infinite_tic_tac_toe.views.components.text_input import StyledTextInput
from infinite_tic_tac_toe.views.theme import ButtonStyle, FontBook, Palette


class LanLobbyScreen(tk.Frame):
    """Two-column LAN Lobby with identical column dimensions, 50px gap, and full-width nickname input."""

    COLUMN_WIDTH = 340
    GAP_WIDTH = 50
    TOTAL_WIDTH = 340 + 50 + 340  # 730px
    ROW_HEIGHT = 74
    BUTTON_HEIGHT = 80

    def __init__(
        self,
        parent: tk.Misc,
        palette: Palette,
        fonts: FontBook,
        styles: Dict[str, ButtonStyle],
        on_back_to_menu: Callable[[], None],
        on_create_room: Callable[[str, str, str], None],  # (player_name, room_code, mark_choice)
        on_join_room: Callable[[str, str], None],         # (player_name, room_code)
        on_cancel_host: Callable[[], None],
    ) -> None:
        super().__init__(parent, bg=palette.bg)
        self._palette = palette
        self._fonts = fonts
        self._styles = styles
        self._on_back_to_menu = on_back_to_menu
        self._on_create_room = on_create_room
        self._on_join_room = on_join_room
        self._on_cancel_host = on_cancel_host

        self._selected_mark: str = "X"
        self._hosting_code: Optional[str] = None
        self._buttons: list[RoundedButton] = []

        self._build_ui()

    def _build_ui(self) -> None:
        p = self._palette
        f = self._fonts

        # Top Bar: Back link at top-left
        top_bar = tk.Frame(self, bg=p.bg)
        top_bar.pack(fill=tk.X, padx=50, pady=(32, 0))

        btn_back = tk.Label(
            top_bar,
            text="← Back to Menu",
            font=f["button_secondary"],
            bg=p.bg,
            fg=p.text_dim,
            cursor="hand2",
        )
        btn_back.pack(side=tk.LEFT)
        btn_back.bind("<Enter>", lambda e: btn_back.configure(fg=p.x))
        btn_back.bind("<Leave>", lambda e: btn_back.configure(fg=p.text_dim))
        btn_back.bind("<Button-1>", lambda e: self._on_back_to_menu())

        # Header Title: Single horizontal line (Cyan "LAN" + White "MULTIPLAYER")
        header = tk.Frame(self, bg=p.bg)
        header.pack(pady=(16, 24))

        tk.Label(
            header,
            text="LAN ",
            font=f["menu_title"],
            bg=p.bg,
            fg=p.x,
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="MULTIPLAYER",
            font=f["menu_title"],
            bg=p.bg,
            fg=p.text,
        ).pack(side=tk.LEFT)

        # Bottom Area: Docked at the bottom of the screen
        bottom_area = tk.Frame(self, bg=p.bg)
        bottom_area.pack(side=tk.BOTTOM, pady=(0, 36))
        self._bottom_area = bottom_area

        self._status_label = tk.Label(
            bottom_area,
            text="",
            font=f["card_desc"],
            bg=p.bg,
            fg=p.text_dim,
        )
        self._status_label.pack()

        # Center Container (Holds fixed 730px card and cancel button)
        center_area = tk.Frame(self, bg=p.bg)
        center_area.pack(expand=True)
        self._center_area = center_area

        lobby_card = tk.Frame(center_area, bg=p.bg, width=self.TOTAL_WIDTH)
        lobby_card.pack()
        self._lobby_card = lobby_card

        # Top Section: Nickname Input (Matches exact outer ends of both columns: 730px)
        name_section = tk.Frame(lobby_card, bg=p.bg, width=self.TOTAL_WIDTH)
        name_section.pack(fill=tk.X, pady=(0, 24))

        tk.Label(
            name_section,
            text="YOUR NICKNAME",
            font=f["status_idle"],
            bg=p.bg,
            fg=p.text_dim,
        ).pack(anchor="w", pady=(0, 6))

        # width_chars=20 keeps intrinsic reqwidth < TOTAL_WIDTH so card width never shifts
        self._name_input = StyledTextInput(
            name_section,
            p,
            f,
            placeholder="Enter your nickname...",
            max_length=16,
            on_change=self._on_name_changed,
            font_name="input_large",
            width_chars=20,
            pady=13,
            padx=16,
        )
        self._name_input.pack(fill=tk.X, expand=True)

        # Two-Column Section with Grid: Left (Host) | Gap & Divider (50px) | Right (Join)
        self._columns_row = tk.Frame(lobby_card, bg=p.bg, width=self.TOTAL_WIDTH)
        self._columns_row.pack(fill=tk.X)
        self._columns_row.columnconfigure(0, weight=0, minsize=self.COLUMN_WIDTH)
        self._columns_row.columnconfigure(1, weight=0, minsize=self.GAP_WIDTH)
        self._columns_row.columnconfigure(2, weight=0, minsize=self.COLUMN_WIDTH)

        action_button_style = self._styles.get(
            "lobby_action", self._styles.get("menu_primary", self._styles["secondary"])
        )

        # --- LEFT COLUMN: HOST A GAME (Width: 340px) ---
        self._col_host = tk.Frame(self._columns_row, bg=p.bg, width=self.COLUMN_WIDTH)
        self._col_host.grid(row=0, column=0, sticky="nsew")

        tk.Label(
            self._col_host,
            text="HOST A GAME",
            font=f["section"],
            bg=p.bg,
            fg=p.x,
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            self._col_host,
            text="PLAY AS",
            font=f["status_idle"],
            bg=p.bg,
            fg=p.text_dim,
        ).pack(anchor="w", pady=(0, 6))

        # Mark Selector Container (Fixed height = ROW_HEIGHT = 74px, grid_propagate=False)
        mark_box = tk.Frame(self._col_host, bg=p.bg, height=self.ROW_HEIGHT)
        mark_box.grid_propagate(False)
        mark_box.pack_propagate(False)
        mark_box.pack(fill=tk.X, pady=(0, 20))
        mark_box.rowconfigure(0, weight=1)
        mark_box.columnconfigure(0, weight=1, uniform="mark")
        mark_box.columnconfigure(1, weight=1, uniform="mark")
        mark_box.columnconfigure(2, weight=1, uniform="mark")

        self._mark_buttons: Dict[str, tk.Label] = {}
        for i, (mark_id, label_text, color) in enumerate(
            (("X", "X", p.x), ("O", "O", p.o), ("RANDOM", "🎲", p.gold))
        ):
            lbl = tk.Label(
                mark_box,
                text=label_text,
                font=f["badge"],
                bg=p.surface if mark_id == "X" else p.input_bg,
                fg=color,
                cursor="hand2",
                highlightthickness=2 if mark_id == "X" else 1,
                highlightbackground=color if mark_id == "X" else p.card_border,
            )
            lbl.grid(row=0, column=i, sticky="nsew", padx=2)
            lbl.bind("<Button-1>", lambda e, m=mark_id: self._select_mark(m))
            self._mark_buttons[mark_id] = lbl

        # Create Button (Height: 80px)
        self._btn_create = RoundedButton(
            self._col_host,
            "Create Room",
            self._handle_create_click,
            action_button_style,
            f,
            p.bg,
            height=self.BUTTON_HEIGHT,
            width=self.COLUMN_WIDTH,
            corner_radius=0,
            border_color=action_button_style.border,
            hover_border_color=action_button_style.hover_border,
            border_width=action_button_style.border_width,
        )
        self._btn_create.pack(fill=tk.X)
        self._buttons.append(self._btn_create)

        # --- VERTICAL DIVIDER WITH 50px GAP ---
        divider_box = tk.Frame(self._columns_row, bg=p.bg, width=self.GAP_WIDTH)
        divider_box.grid(row=0, column=1, sticky="ns")
        divider_box.pack_propagate(False)

        divider = tk.Frame(divider_box, bg=p.divider, width=1)
        divider.pack(expand=True, fill=tk.Y, pady=6)

        # --- RIGHT COLUMN: JOIN A GAME (Width: 340px) ---
        self._col_join = tk.Frame(self._columns_row, bg=p.bg, width=self.COLUMN_WIDTH)
        self._col_join.grid(row=0, column=2, sticky="nsew")

        tk.Label(
            self._col_join,
            text="JOIN A GAME",
            font=f["section"],
            bg=p.bg,
            fg=p.o,
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            self._col_join,
            text="ROOM CODE",
            font=f["status_idle"],
            bg=p.bg,
            fg=p.text_dim,
        ).pack(anchor="w", pady=(0, 6))

        # Room Code Container (Fixed height = ROW_HEIGHT = 74px)
        code_box = tk.Frame(self._col_join, bg=p.bg, height=self.ROW_HEIGHT)
        code_box.pack_propagate(False)
        code_box.pack(fill=tk.X, pady=(0, 20))

        self._code_input = StyledTextInput(
            code_box,
            p,
            f,
            placeholder="Room code...",
            uppercase=True,
            max_length=15,
            on_change=self._on_code_changed,
            font_name="input_large",
            width_chars=12,
            pady=12,
            padx=12,
            justify="center",
        )
        self._code_input.pack(fill=tk.BOTH, expand=True)

        # Join Button (Height: 80px)
        self._btn_join = RoundedButton(
            self._col_join,
            "Join Game",
            self._handle_join_click,
            action_button_style,
            f,
            p.bg,
            height=self.BUTTON_HEIGHT,
            width=self.COLUMN_WIDTH,
            corner_radius=0,
            border_color=action_button_style.border,
            hover_border_color=action_button_style.hover_border,
            border_width=action_button_style.border_width,
        )
        self._btn_join.pack(fill=tk.X)
        self._buttons.append(self._btn_join)

        # --- HOSTING VIEW: FULL-WIDTH ROOM CODE CARD (730px, fixed height: 130px) ---
        self._hosting_frame = tk.Frame(
            lobby_card,
            bg=p.surface,
            highlightbackground=p.card_border,
            highlightthickness=1,
            width=self.TOTAL_WIDTH,
            height=130,
        )
        self._hosting_frame.pack_propagate(False)

        inner_hosting = tk.Frame(self._hosting_frame, bg=p.surface)
        inner_hosting.pack(expand=True)

        tk.Label(
            inner_hosting,
            text="ROOM CODE",
            font=f["status_idle"],
            bg=p.surface,
            fg=p.text_dim,
        ).pack(pady=(0, 8))

        self._code_label = tk.Label(
            inner_hosting,
            text="",
            font=f["code_display"],
            bg=p.surface,
            fg=p.gold,
        )
        self._code_label.pack()

        # Cancel Hosting link: styled identically to 'Back to Menu' in center_area below card
        self._btn_cancel_host = tk.Label(
            center_area,
            text="Cancel Hosting",
            font=f["button_secondary"],
            bg=p.bg,
            fg=p.text_dim,
            cursor="hand2",
        )
        self._btn_cancel_host.bind("<Enter>", lambda e: self._btn_cancel_host.configure(fg=p.x))
        self._btn_cancel_host.bind("<Leave>", lambda e: self._btn_cancel_host.configure(fg=p.text_dim))
        self._btn_cancel_host.bind("<Button-1>", lambda e: self._handle_cancel_host())
        self._btn_cancel = self._btn_cancel_host  # alias for backwards compatibility

        self._update_controls_state()

    # -- Interaction Handlers ------------------------------------------------

    def _select_mark(self, mark: str) -> None:
        self._selected_mark = mark
        p = self._palette
        colors = {"X": p.x, "O": p.o, "RANDOM": p.gold}
        for m_id, lbl in self._mark_buttons.items():
            if m_id == mark:
                lbl.configure(
                    bg=p.surface,
                    highlightbackground=colors[m_id],
                    highlightthickness=2,
                )
            else:
                lbl.configure(
                    bg=p.input_bg,
                    highlightbackground=p.card_border,
                    highlightthickness=1,
                )

    def _on_name_changed(self, name: str) -> None:
        self._update_controls_state()

    def _on_code_changed(self, code: str) -> None:
        self._update_controls_state()

    def _update_controls_state(self) -> None:
        has_name = bool(self._name_input.get_value().strip())
        has_code = bool(self._code_input.get_value().strip())

        self._btn_create.set_enabled(has_name)
        self._btn_join.set_enabled(has_name and has_code)

        if not has_name:
            self._status_label.configure(
                text="Enter a nickname above to enable Create and Join.",
                fg=self._palette.text_dim,
            )
        elif not has_code:
            self._status_label.configure(
                text="Create a room to host, or enter your friend's code on the right to join.",
                fg=self._palette.text_muted,
            )
        else:
            self._status_label.configure(
                text=f"Ready to connect to room {self._code_input.get_value()}.",
                fg=self._palette.x,
            )

    def _handle_create_click(self) -> None:
        name = self._name_input.get_value().strip()
        if not name:
            return
        code = generate_room_code()
        self._hosting_code = code

        # 1. Lock the nickname input
        self._name_input.set_locked(True)

        # 2. Hide two-column section completely (no Host/Join columns)
        self._columns_row.pack_forget()

        # 3. Show full-width Room Code card inside lobby_card
        self._code_label.configure(text=code)
        self._hosting_frame.pack(fill=tk.X)

        # 4. Show centered Cancel Hosting link directly below card in center_area
        self._btn_cancel_host.pack(pady=(24, 0))

        # 5. Show yellow status text docked at the bottom of the screen
        self._status_label.configure(
            text=f"Broadcasting room {code} on LAN. Waiting for opponent...",
            fg=self._palette.gold,
        )

        self._on_create_room(name, code, self._selected_mark)

    def _handle_cancel_host(self) -> None:
        self._hosting_code = None

        # 1. Hide full-width hosting frame and cancel link
        self._hosting_frame.pack_forget()
        self._btn_cancel_host.pack_forget()

        # 2. Restore two-column layout
        self._columns_row.pack(fill=tk.X)

        # 3. Unlock nickname input
        self._name_input.set_locked(False)

        # 4. Restore idle controls and status
        self._update_controls_state()
        self._on_cancel_host()

    def _handle_join_click(self) -> None:
        name = self._name_input.get_value().strip()
        code = self._code_input.get_value().strip()
        if not (name and code):
            return

        self._status_label.configure(
            text=f"Searching for room {code} on LAN...",
            fg=self._palette.x,
        )
        self._on_join_room(name, code)

    def show_error(self, message: str) -> None:
        self._status_label.configure(text=message, fg="#ef4444")

    def redraw_buttons(self) -> None:
        for b in self._buttons:
            b.redraw()
