"""Application navigator managing top-level screens, mode selection, and LAN matchmaking."""

from __future__ import annotations

import random
import sys
import tkinter as tk
from pathlib import Path
from typing import Optional

from infinite_tic_tac_toe.controllers.game_controller import GameController
from infinite_tic_tac_toe.network.connection import (
    LanClient,
    LanHost,
    NetworkConnection,
)
from infinite_tic_tac_toe.network.discovery import (
    LanBroadcaster,
    LanScanner,
    RoomBeacon,
)
from infinite_tic_tac_toe.network.protocol import MessageType
from infinite_tic_tac_toe.views import (
    DEFAULT_WINDOW,
    MIN_WINDOW,
    PALETTE,
    FontBook,
    LanLobbyScreen,
    MainMenuScreen,
    RulesDialog,
    build_button_styles,
)


class AppNavigator:
    """Root application navigator and screen router."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.palette = PALETTE
        self.fonts = FontBook(root)
        self.styles = build_button_styles(self.palette)

        self._current_screen: Optional[tk.Widget] = None
        self._current_game: Optional[GameController] = None

        # Network session holders
        self._host: Optional[LanHost] = None
        self._broadcaster: Optional[LanBroadcaster] = None
        self._scanner: Optional[LanScanner] = None

        self._configure_window()
        self._container = tk.Frame(root, bg=self.palette.bg)
        self._container.pack(fill=tk.BOTH, expand=True)

        self.show_main_menu()

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

        # Set application window icon (dock, taskbar, alt-tab, and title bar)
        self._app_icons: list[tk.PhotoImage] = []
        try:
            # Check package-internal assets first (for uvx/pip), then repo root
            candidates = [
                Path(__file__).resolve().parent.parent / "assets",
                Path(__file__).resolve().parent.parent.parent.parent / "assets",
            ]
            asset_dir = next((d for d in candidates if d.is_dir()), None)
            if asset_dir:
                ico_file = asset_dir / "icon.ico"
                png_256 = asset_dir / "app_icon.png"
                png_64 = asset_dir / "app_icon_64.png"
                png_logo = asset_dir / "logo.png"

                # Windows native window icon bitmap
                if sys.platform.startswith("win") and ico_file.is_file():
                    try:
                        self.root.iconbitmap(default=str(ico_file))
                    except Exception:
                        pass

                # Universal cross-platform window icon (X11, Wayland, Windows taskbar)
                for path in (png_256, png_64, png_logo):
                    if path.is_file():
                        try:
                            self._app_icons.append(tk.PhotoImage(file=str(path)))
                        except Exception:
                            pass

                if self._app_icons:
                    self.root.iconphoto(True, *self._app_icons)
        except Exception:
            pass

    def _clear_current_screen(self) -> None:
        self._cleanup_network()
        if self._current_game:
            self._current_game.destroy()
            self._current_game = None
        if self._current_screen:
            self._current_screen.destroy()
            self._current_screen = None

    def _cleanup_network(self) -> None:
        if self._broadcaster:
            self._broadcaster.stop()
            self._broadcaster = None
        if self._host:
            self._host.close()
            self._host = None
        if self._scanner:
            self._scanner.stop()
            self._scanner = None

    # -- Screens -------------------------------------------------------------

    def show_main_menu(self) -> None:
        self._clear_current_screen()
        screen = MainMenuScreen(
            self._container,
            self.palette,
            self.fonts,
            self.styles,
            on_start_local=self.start_local_game,
            on_start_lan=self.show_lan_lobby,
            on_show_rules=self.show_rules,
        )
        screen.pack(fill=tk.BOTH, expand=True)
        self._current_screen = screen

    def start_local_game(self) -> None:
        self._clear_current_screen()
        game = GameController(
            self._container,
            network_conn=None,
            on_leave_game=self.show_main_menu,
        )
        self._current_game = game
        self._current_screen = game.screen

    def show_lan_lobby(self) -> None:
        self._clear_current_screen()
        screen = LanLobbyScreen(
            self._container,
            self.palette,
            self.fonts,
            self.styles,
            on_back_to_menu=self.show_main_menu,
            on_create_room=self.handle_create_room,
            on_join_room=self.handle_join_room,
            on_cancel_host=self._cleanup_network,
        )
        screen.pack(fill=tk.BOTH, expand=True)
        self._current_screen = screen

    def show_rules(self) -> None:
        RulesDialog(self.root, self.palette, self.fonts, self.styles)

    # -- LAN Hosting ---------------------------------------------------------

    def handle_create_room(self, host_name: str, code: str, mark_choice: str) -> None:
        self._cleanup_network()

        # Resolve starting mark
        if mark_choice == "RANDOM":
            host_mark = random.choice(("X", "O"))
        else:
            host_mark = mark_choice

        def on_client_connected(conn: NetworkConnection) -> None:
            # Dispatch safely to Tkinter main thread
            self.root.after(0, lambda: self._on_host_got_client(conn, host_name, host_mark))

        self._host = LanHost(on_connected=on_client_connected)

        beacon = RoomBeacon(
            code=code,
            host_name=host_name,
            tcp_port=self._host.port,
            host_mark=host_mark,
        )
        self._broadcaster = LanBroadcaster(beacon=beacon)
        self._broadcaster.start()

    def _on_host_got_client(self, conn: NetworkConnection, host_name: str, host_mark: str) -> None:
        guest_mark = "O" if host_mark == "X" else "X"
        # Stop broadcaster once connected
        if self._broadcaster:
            self._broadcaster.stop()
            self._broadcaster = None

        # Send initial handshake to guest
        conn.send_message(
            MessageType.HANDSHAKE,
            sender_name=host_name,
            assigned_mark=guest_mark,
        )

        # Wait for guest handshake response in poll loop
        def check_guest_handshake() -> None:
            msgs = conn.poll_messages()
            for m in msgs:
                if m.get("type") == MessageType.HANDSHAKE:
                    guest_name = m.get("sender_name", "Opponent")
                    self._launch_lan_game(
                        conn=conn,
                        my_mark=host_mark,
                        my_name=host_name,
                        opponent_name=guest_name,
                    )
                    return
            if conn.is_connected:
                self.root.after(50, check_guest_handshake)

        check_guest_handshake()

    # -- LAN Joining ---------------------------------------------------------

    def handle_join_room(self, player_name: str, code_or_target: str) -> None:
        self._cleanup_network()
        code_or_target = code_or_target.strip()

        # Check if direct IP:PORT was entered
        if ":" in code_or_target:
            try:
                ip, port_str = code_or_target.split(":", 1)
                self._connect_to_host(ip, int(port_str), player_name)
                return
            except Exception:
                pass

        # Otherwise search on LAN via UDP beacon scanner
        def on_beacon_found(host_ip: str, tcp_port: int, beacon: RoomBeacon) -> None:
            self.root.after(0, lambda: self._connect_to_host(host_ip, tcp_port, player_name))

        self._scanner = LanScanner(target_code=code_or_target, on_found=on_beacon_found)
        self._scanner.start()

        # 8-second timeout for discovery
        self.root.after(8000, lambda: self._check_scan_timeout(code_or_target))

    def _check_scan_timeout(self, code: str) -> None:
        if self._scanner and self._scanner._running:
            self._scanner.stop()
            self._scanner = None
            if isinstance(self._current_screen, LanLobbyScreen):
                self._current_screen.show_error(
                    f"Room '{code}' not found on LAN. Ensure both devices are on the same Wi-Fi.",
                )

    def _connect_to_host(self, host_ip: str, port: int, player_name: str) -> None:
        if self._scanner:
            self._scanner.stop()
            self._scanner = None

        conn = LanClient.connect(host_ip, port)
        if not conn:
            if isinstance(self._current_screen, LanLobbyScreen):
                self._current_screen.show_error(f"Failed to connect to {host_ip}:{port}.")
            return

        # Wait for host handshake specifying assigned mark
        def check_host_handshake() -> None:
            msgs = conn.poll_messages()
            for m in msgs:
                if m.get("type") == MessageType.HANDSHAKE:
                    assigned_mark = m.get("assigned_mark", "O")
                    host_name = m.get("sender_name", "Host")
                    # Respond with guest handshake
                    conn.send_message(
                        MessageType.HANDSHAKE,
                        sender_name=player_name,
                    )
                    self._launch_lan_game(
                        conn=conn,
                        my_mark=assigned_mark,
                        my_name=player_name,
                        opponent_name=host_name,
                    )
                    return
            if conn.is_connected:
                self.root.after(50, check_host_handshake)

        check_host_handshake()

    # -- Game Launch ---------------------------------------------------------

    def _launch_lan_game(
        self,
        conn: NetworkConnection,
        my_mark: str,
        my_name: str,
        opponent_name: str,
    ) -> None:
        self._clear_current_screen()
        game = GameController(
            self._container,
            network_conn=conn,
            my_mark=my_mark,
            my_name=my_name,
            opponent_name=opponent_name,
            on_leave_game=self.show_main_menu,
        )
        self._current_game = game
        self._current_screen = game.screen
