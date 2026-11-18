"""Game controller coordinating game model, views, local clicks, and LAN network events."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Dict, Optional

from infinite_tic_tac_toe.models import GameSession, InfiniteTicTacToeLogic
from infinite_tic_tac_toe.network.connection import NetworkConnection
from infinite_tic_tac_toe.network.protocol import MessageType
from infinite_tic_tac_toe.views import (
    DEFAULT_WINDOW,
    MIN_WINDOW,
    PALETTE,
    FontBook,
    GameScreen,
    RulesDialog,
    SidebarActions,
    build_button_styles,
)


class GameController:
    """Manages an active game session, wiring views, local input, and LAN messages."""

    MIN_SCALE = 0.7
    MAX_SCALE = 1.2
    SCALE_EPSILON = 0.02
    NETWORK_POLL_MS = 33

    def __init__(
        self,
        parent: tk.Misc,
        network_conn: Optional[NetworkConnection] = None,
        my_mark: str = "X",
        my_name: str = "Player X",
        opponent_name: str = "Player O",
        on_leave_game: Optional[Callable[[], None]] = None,
    ) -> None:
        self.parent = parent
        self.root = parent.winfo_toplevel()
        self.network_conn = network_conn
        self.my_mark = my_mark
        self.my_name = my_name
        self.opponent_name = opponent_name
        self.on_leave_game = on_leave_game

        self.palette = PALETTE
        self.game = InfiniteTicTacToeLogic()
        self.session = GameSession()
        self.is_fullscreen = False
        self._scale = 1.0
        self._poll_job: Optional[str] = None

        self._configure_root_if_needed()
        self.fonts = FontBook(self.root)
        self.styles = build_button_styles(self.palette)

        self._build_screen()
        self._bind_events()
        self._refresh_all()

        if self.network_conn:
            self._schedule_network_poll()

    @property
    def scores(self) -> Dict[str, int]:
        return self.session.scores

    @scores.setter
    def scores(self, val: Dict[str, int]) -> None:
        self.session.scores = val

    @property
    def round_number(self) -> int:
        return self.session.round_number

    @round_number.setter
    def round_number(self, val: int) -> None:
        self.session.round_number = val

    # -- construction --------------------------------------------------------

    def _configure_root_if_needed(self) -> None:
        # Only configure window if parent is root
        if self.parent is self.root:
            self.root.title("Infinite Tic-Tac-Toe")
            self.root.geometry(f"{DEFAULT_WINDOW[0]}x{DEFAULT_WINDOW[1]}")
            self.root.minsize(*MIN_WINDOW)
            self.root.configure(bg=self.palette.bg)

    def _build_screen(self) -> None:
        actions = SidebarActions(
            new_round=self.on_new_round,
            reset_scores=self.on_reset_all,
            show_rules=self.show_rules,
            toggle_fullscreen=self._toggle_fullscreen,
            leave_game=self._handle_leave_game if self.on_leave_game else None,
        )

        self.screen = GameScreen(
            self.parent,
            self.palette,
            self.fonts,
            self.styles,
            self.game,
            actions,
            on_cell_click=self._handle_cell_click,
        )
        self.screen.pack(fill=tk.BOTH, expand=True)

        # Expose widgets directly for compatibility
        self.sidebar = self.screen.sidebar
        self.board_view = self.screen.board_view
        self.banner = self.screen.banner

        # Set player names on sidebar cards
        if self.network_conn:
            x_name = f"{self.my_name} (You)" if self.my_mark == "X" else self.opponent_name
            o_name = f"{self.my_name} (You)" if self.my_mark == "O" else self.opponent_name
            self.sidebar.update_player_labels(x_name, o_name)

    def _bind_events(self) -> None:
        self.root.bind("<r>", lambda e: self.on_new_round())
        self.root.bind("<R>", lambda e: self.on_new_round())
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)
        self.root.bind("<Configure>", self._on_root_configure)

    def destroy(self) -> None:
        """Tear down controller, screen, and cancel background polls."""
        if self._poll_job is not None:
            self.root.after_cancel(self._poll_job)
            self._poll_job = None
        if self.network_conn:
            self.network_conn.send_message(MessageType.LEAVE, reason="Player quit")
            self.network_conn.close()
            self.network_conn = None
        self.screen.destroy()

    # -- window handling -----------------------------------------------------

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

    def _on_root_configure(self, event: tk.Event) -> None:
        if event.widget is not self.root:
            return
        factor = min(event.width / DEFAULT_WINDOW[0], event.height / DEFAULT_WINDOW[1])
        factor = max(self.MIN_SCALE, min(self.MAX_SCALE, factor))
        if abs(factor - self._scale) < self.SCALE_EPSILON:
            return

        self._scale = factor
        self.fonts.rescale(factor)
        self.screen.redraw_widgets()

    # -- view updates --------------------------------------------------------

    def _refresh_all(self) -> None:
        self.sidebar.update_players(self.game, self.session.scores)
        self.sidebar.set_button_enabled("new_round", not self.game.is_empty)
        self._show_round()
        self.board_view.render()

    def _show_round(self) -> None:
        if self.network_conn and not self.game.game_over:
            if self.game.current_player == self.my_mark:
                self.banner.set(f"ROUND {self.session.round_number} — YOUR TURN ({self.my_mark})", self.palette.x if self.my_mark == "X" else self.palette.o)
            else:
                self.banner.set(f"ROUND {self.session.round_number} — OPPONENT'S TURN", self.palette.text_dim)
        else:
            self.banner.set(f"ROUND {self.session.round_number}")

    def _show_winner(self, winner: str) -> None:
        if self.network_conn:
            if winner == self.my_mark:
                self.banner.set(f"🎉 YOU WON ROUND {self.session.round_number}!", self.palette.gold)
            else:
                self.banner.set(f"PLAYER {winner} WON ROUND {self.session.round_number}!", self.palette.text)
        else:
            self.banner.set(f"PLAYER {winner} WINS ROUND {self.session.round_number}!")

    # -- move handling -------------------------------------------------------

    def _handle_cell_click(self, r: int, c: int) -> None:
        if self.network_conn:
            # Enforce turn in LAN mode
            if self.game.current_player != self.my_mark:
                return

        if not self.game.is_valid_move(r, c):
            return

        result = self.game.make_move(r, c)
        if not result["success"]:
            return

        if self.network_conn:
            self.network_conn.send_message(
                MessageType.MOVE,
                r=r,
                c=c,
                player=result["player"],
            )

        self._apply_move_effects(result)

    def _apply_move_effects(self, result: Dict[str, Any]) -> None:
        if result["vanished"]:
            self.board_view.play_vanish(tuple(result["vanished"]), result["player"])

        if result["game_over"]:
            winner = result["winner"]
            self.session.record_win(winner)
            self.sidebar.update_players(self.game, self.session.scores)
            self._show_winner(winner)
            self.board_view.play_win()
        else:
            self.sidebar.update_players(self.game, self.session.scores)
            self._show_round()

        self.sidebar.set_button_enabled("new_round", not self.game.is_empty)
        self.board_view.render()

    # -- game actions --------------------------------------------------------

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

        self.session.next_round()
        self.game.reset(alternate_starting=True)
        self.board_view.clear_effects()
        self._refresh_all()

        if self.network_conn:
            self.network_conn.send_message(
                MessageType.NEW_ROUND,
                round_number=self.session.round_number,
                starting_player=self.game.starting_player,
            )

    def on_reset_all(self) -> None:
        if self.session.has_progress and not messagebox.askyesno(
            "Reset Scores",
            "Are you sure you want to reset all scores and start over?",
            parent=self.root,
        ):
            return

        self.session.reset_all()
        self.game.reset(alternate_starting=False)
        self.board_view.clear_effects()
        self._refresh_all()

        if self.network_conn:
            self.network_conn.send_message(MessageType.RESET_SCORES)

    def show_rules(self) -> None:
        RulesDialog(self.root, self.palette, self.fonts, self.styles)

    def _handle_leave_game(self) -> None:
        if messagebox.askyesno("Leave Game", "Return to the main menu?", parent=self.root):
            if self.on_leave_game:
                self.on_leave_game()

    # -- LAN polling loop ----------------------------------------------------

    def _schedule_network_poll(self) -> None:
        self._process_network_messages()
        if self.network_conn and self.network_conn.is_connected:
            self._poll_job = self.root.after(self.NETWORK_POLL_MS, self._schedule_network_poll)

    def _process_network_messages(self) -> None:
        if not self.network_conn:
            return

        messages = self.network_conn.poll_messages()
        for msg in messages:
            m_type = msg.get("type")
            if m_type == MessageType.MOVE:
                r, c = msg["r"], msg["c"]
                if self.game.is_valid_move(r, c):
                    result = self.game.make_move(r, c)
                    self._apply_move_effects(result)
            elif m_type == MessageType.NEW_ROUND:
                self.session.round_number = msg.get("round_number", self.session.round_number + 1)
                self.game.reset(alternate_starting=True)
                self.board_view.clear_effects()
                self._refresh_all()
            elif m_type == MessageType.RESET_SCORES:
                self.session.reset_all()
                self.game.reset(alternate_starting=False)
                self.board_view.clear_effects()
                self._refresh_all()
            elif m_type == MessageType.LEAVE:
                messagebox.showinfo("Game Ended", f"Opponent disconnected ({msg.get('reason', '')}).", parent=self.root)
                if self.on_leave_game:
                    self.on_leave_game()
                break


# Alias for backward compatibility
InfiniteTicTacToeApp = GameController


def main() -> None:
    root = tk.Tk()
    GameController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
