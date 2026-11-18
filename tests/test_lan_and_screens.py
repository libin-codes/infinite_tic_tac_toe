import time
import tkinter as tk
import unittest

from infinite_tic_tac_toe.controllers.app_navigator import AppNavigator
from infinite_tic_tac_toe.controllers.game_controller import GameController
from infinite_tic_tac_toe.network.connection import LanClient, LanHost
from infinite_tic_tac_toe.views.screens.lan_lobby import LanLobbyScreen
from infinite_tic_tac_toe.views.screens.main_menu import MainMenuScreen


class TestLANAndScreens(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_app_navigator_startup(self):
        nav = AppNavigator(self.root)
        self.assertIsInstance(nav._current_screen, MainMenuScreen)
        assert isinstance(nav._current_screen, MainMenuScreen)
        menu = nav._current_screen
        self.assertEqual(menu.BUTTON_HEIGHT, 145)
        self.assertEqual(menu.BUTTON_WIDTH, 520)
        self.assertEqual(menu._buttons[0]._corner_radius, 0)

        # Test how to play link opens rules dialog
        rules_called = []
        menu._on_show_rules = lambda: rules_called.append(True)
        menu._open_how_to_play()
        self.assertEqual(len(rules_called), 1)

        # Transition to LAN Lobby
        nav.show_lan_lobby()
        self.assertIsInstance(nav._current_screen, LanLobbyScreen)

        # Transition to Local Game
        nav.start_local_game()
        self.assertIsInstance(nav._current_game, GameController)
        assert isinstance(nav._current_game, GameController)
        self.assertFalse(nav._current_game.game.game_over)

        # Return to Main Menu
        nav.show_main_menu()
        self.assertIsInstance(nav._current_screen, MainMenuScreen)
        nav._clear_current_screen()
        self.root.withdraw()

    def test_lan_lobby_name_unlock(self):
        nav = AppNavigator(self.root)
        nav.show_lan_lobby()
        self.assertIsInstance(nav._current_screen, LanLobbyScreen)
        assert isinstance(nav._current_screen, LanLobbyScreen)
        lobby = nav._current_screen

        # Initially buttons are disabled
        self.assertFalse(lobby._btn_create.enabled)
        self.assertFalse(lobby._btn_join.enabled)

        # Enter name
        lobby._name_input.set_value("Alice")
        lobby._on_name_changed("Alice")
        self.assertTrue(lobby._btn_create.enabled)
        self.assertFalse(lobby._btn_join.enabled)  # Code is still empty

        # Enter room code
        lobby._code_input.set_value("K9X2")
        lobby._on_code_changed("K9X2")
        self.assertTrue(lobby._btn_create.enabled)
        self.assertTrue(lobby._btn_join.enabled)

        # Clearing name disables both again
        lobby._name_input.set_value("")
        lobby._on_name_changed("")
        self.assertFalse(lobby._btn_create.enabled)
        self.assertFalse(lobby._btn_join.enabled)

        nav._clear_current_screen()
        self.root.withdraw()

    def test_lan_lobby_dimensions_and_hosting_flow(self):
        self.root.deiconify()
        nav = AppNavigator(self.root)
        nav.show_lan_lobby()
        self.assertIsInstance(nav._current_screen, LanLobbyScreen)
        assert isinstance(nav._current_screen, LanLobbyScreen)
        lobby = nav._current_screen

        # Check geometry constants
        self.assertEqual(lobby.COLUMN_WIDTH, 340)
        self.assertEqual(lobby.GAP_WIDTH, 50)
        self.assertEqual(lobby.TOTAL_WIDTH, 730)
        self.assertEqual(lobby.BUTTON_HEIGHT, 80)
        self.assertEqual(lobby.ROW_HEIGHT, 74)

        # Verify width stability when typing
        self.root.update()
        w_initial = lobby._lobby_card.winfo_width()
        self.assertEqual(w_initial, 730)

        lobby._name_input.set_value("A")
        lobby._on_name_changed("A")
        self.root.update()
        self.assertEqual(lobby._lobby_card.winfo_width(), 730)

        lobby._name_input.set_value("HostPlayer")
        lobby._on_name_changed("HostPlayer")
        self.root.update()
        self.assertEqual(lobby._lobby_card.winfo_width(), 730)

        self.assertTrue(lobby._btn_create.enabled)
        self.assertFalse(lobby._name_input.locked)

        # Before create: columns_row is packed, hosting_frame is not packed
        self.assertTrue(lobby._columns_row.winfo_manager() == "pack")
        self.assertFalse(lobby._hosting_frame.winfo_manager() == "pack")

        created_rooms = []
        lobby._on_create_room = lambda name, code, mark: created_rooms.append((name, code, mark))
        lobby._handle_create_click()

        # After create: nickname input is locked
        self.assertTrue(lobby._name_input.locked)

        # Two-column section is hidden
        self.assertFalse(lobby._columns_row.winfo_manager() == "pack")

        # Full-width hosting frame is visible
        self.assertTrue(lobby._hosting_frame.winfo_manager() == "pack")
        self.root.update()
        self.assertEqual(lobby._lobby_card.winfo_width(), 730)
        code = lobby._hosting_code
        self.assertIsNotNone(code)
        self.assertEqual(lobby._code_label.cget("text"), code)

        # Status text contains both broadcasting and opponent clause in yellow
        status_text = lobby._status_label.cget("text")
        self.assertEqual(status_text, f"Broadcasting room {code} on LAN. Waiting for opponent...")

        # Cancel button link is packed
        self.assertTrue(lobby._btn_cancel_host.winfo_manager() == "pack")
        self.assertTrue(lobby._btn_cancel.winfo_manager() == "pack")

        # Now cancel hosting
        cancel_called = []
        lobby._on_cancel_host = lambda: cancel_called.append(True)
        lobby._handle_cancel_host()

        # Nickname input unlocked, columns restored, hosting frame & cancel link hidden
        self.root.update()
        self.assertEqual(lobby._lobby_card.winfo_width(), 730)
        self.assertFalse(lobby._name_input.locked)
        self.assertTrue(lobby._columns_row.winfo_manager() == "pack")
        self.assertFalse(lobby._hosting_frame.winfo_manager() == "pack")
        self.assertFalse(lobby._btn_cancel_host.winfo_manager() == "pack")
        self.assertEqual(len(cancel_called), 1)

        nav._clear_current_screen()
        self.root.withdraw()

    def test_lan_game_turn_enforcement_and_move_sync(self):
        # Setup host and client connections
        host_box = []
        host_srv = LanHost(on_connected=lambda conn: host_box.append(conn))
        client_conn = LanClient.connect("127.0.0.1", host_srv.port)
        assert client_conn is not None

        timeout = time.time() + 2.0
        while not host_box and time.time() < timeout:
            time.sleep(0.05)

        host_conn = host_box[0]

        # Create two GameControllers: one host (Player X), one guest (Player O)
        host_game = GameController(
            self.root,
            network_conn=host_conn,
            my_mark="X",
            my_name="HostPlayer",
            opponent_name="GuestPlayer",
        )

        guest_game = GameController(
            self.root,
            network_conn=client_conn,
            my_mark="O",
            my_name="GuestPlayer",
            opponent_name="HostPlayer",
        )

        # Initially current_player is "X"
        self.assertEqual(host_game.game.current_player, "X")
        self.assertEqual(guest_game.game.current_player, "X")

        # Guest (O) tries to click (0, 0) out of turn -> should be ignored!
        guest_game._handle_cell_click(0, 0)
        self.assertIsNone(guest_game.game.board[0][0])
        self.assertTrue(guest_game.game.is_empty)

        # Host (X) clicks (0, 0) -> valid!
        host_game._handle_cell_click(0, 0)
        self.assertEqual(host_game.game.board[0][0], "X")
        self.assertEqual(host_game.game.current_player, "O")

        # Process network packets on guest
        timeout = time.time() + 2.0
        while guest_game.game.board[0][0] is None and time.time() < timeout:
            guest_game._process_network_messages()
            time.sleep(0.05)

        self.assertEqual(guest_game.game.board[0][0], "X")
        self.assertEqual(guest_game.game.current_player, "O")

        # Now it is Guest's turn! Guest clicks (1, 1)
        guest_game._handle_cell_click(1, 1)
        self.assertEqual(guest_game.game.board[1][1], "O")
        self.assertEqual(guest_game.game.current_player, "X")

        # Process on host
        timeout = time.time() + 2.0
        while host_game.game.board[1][1] is None and time.time() < timeout:
            host_game._process_network_messages()
            time.sleep(0.05)

        self.assertEqual(host_game.game.board[1][1], "O")
        self.assertEqual(host_game.game.current_player, "X")

        # Cleanup
        host_game.destroy()
        guest_game.destroy()
        client_conn.close()
        host_conn.close()
        host_srv.close()


if __name__ == "__main__":
    unittest.main()
