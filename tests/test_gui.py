import unittest
from unittest.mock import patch
import tkinter as tk
from infinite_tic_tac_toe.controllers import GameController, InfiniteTicTacToeApp
from infinite_tic_tac_toe.views import blend_hex_colors


class TestGUI(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = GameController(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_alias(self):
        self.assertIs(GameController, InfiniteTicTacToeApp)

    def test_blend_colors(self):
        c = blend_hex_colors("#000000", "#ffffff", 0.5)
        self.assertEqual(c, "#7f7f7f")
        c0 = blend_hex_colors("#112233", "#ffffff", 0.0)
        self.assertEqual(c0, "#112233")
        c1 = blend_hex_colors("#112233", "#ffffff", 1.0)
        self.assertEqual(c1, "#ffffff")

    def test_initial_app_state(self):
        self.assertEqual(self.app.round_number, 1)
        self.assertEqual(self.app.scores, {"X": 0, "O": 0})
        self.assertFalse(self.app.game.game_over)
        self.assertEqual(self.app.game.current_player, "X")
        # New round button is disabled when board is empty
        self.assertFalse(self.app.sidebar.buttons["new_round"].enabled)

    def test_player_cards_content(self):
        card_x = self.app.sidebar.cards["X"]
        card_o = self.app.sidebar.cards["O"]

        # Avatar shows X and O
        self.assertEqual(card_x._avatar_label.cget("text"), "X")
        self.assertEqual(card_o._avatar_label.cget("text"), "O")

        # Subtitle shows turn status without wins text
        self.assertEqual(card_x._status.cget("text"), "TURN")
        self.assertEqual(card_o._status.cget("text"), "WAITING")

        # Right side displays bold wins count in white
        self.assertEqual(card_x._wins.cget("text"), "0")
        self.assertEqual(card_o._wins.cget("text"), "0")
        self.assertEqual(card_x._wins.cget("fg"), self.app.palette.text)
        self.assertEqual(card_o._wins.cget("fg"), self.app.palette.text)

    def test_new_round_disabled_when_empty(self):
        # Triggering on_new_round while board is empty does nothing
        self.app.on_new_round()
        self.assertEqual(self.app.round_number, 1)
        self.assertTrue(self.app.game.is_empty)

    def test_simulated_click_and_render(self):
        self.app._handle_cell_click(0, 0)
        self.assertEqual(self.app.game.board[0][0], "X")
        self.assertEqual(self.app.game.current_player, "O")
        # Once a move is placed, New Round button becomes enabled
        self.assertTrue(self.app.sidebar.buttons["new_round"].enabled)

        card_x = self.app.sidebar.cards["X"]
        card_o = self.app.sidebar.cards["O"]
        self.assertEqual(card_x._status.cget("text"), "WAITING")
        self.assertEqual(card_o._status.cget("text"), "TURN")

    def test_new_round_confirmation_when_in_progress(self):
        self.app._handle_cell_click(0, 0)
        self.assertFalse(self.app.game.game_over)
        self.assertFalse(self.app.game.is_empty)

        # Cancel confirmation dialog: round remains unchanged
        with patch("tkinter.messagebox.askyesno", return_value=False) as mock_dialog:
            self.app.on_new_round()
            mock_dialog.assert_called_once()
            self.assertEqual(self.app.round_number, 1)
            self.assertEqual(self.app.game.board[0][0], "X")

        # Accept confirmation dialog: round advances and resets
        with patch("tkinter.messagebox.askyesno", return_value=True) as mock_dialog:
            self.app.on_new_round()
            mock_dialog.assert_called_once()
            self.assertEqual(self.app.round_number, 2)
            self.assertTrue(self.app.game.is_empty)
            self.assertFalse(self.app.sidebar.buttons["new_round"].enabled)

    def test_simulated_game_win(self):
        # Play X win on row 0: (0,0), (1,0), (0,1), (1,1), (0,2)
        moves = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)]
        for r, c in moves:
            self.app._handle_cell_click(r, c)

        self.assertTrue(self.app.game.game_over)
        self.assertEqual(self.app.game.winner, "X")
        self.assertEqual(self.app.scores["X"], 1)

        card_x = self.app.sidebar.cards["X"]
        card_o = self.app.sidebar.cards["O"]
        self.assertEqual(card_x._wins.cget("text"), "1")
        self.assertEqual(card_x._wins.cget("fg"), self.app.palette.text)
        self.assertEqual(card_x._status.cget("text"), "🏆 WINNER")
        self.assertEqual(card_o._wins.cget("text"), "0")
        self.assertEqual(card_o._wins.cget("fg"), self.app.palette.text)
        self.assertEqual(card_o._status.cget("text"), "DEFEAT")

        # Winner banner is white and formatted cleanly without emoji
        self.assertEqual(self.app.banner.cget("text"), "PLAYER X WINS ROUND 1!")
        self.assertEqual(self.app.banner.cget("fg"), self.app.palette.text)

        # Trigger new round
        self.app.on_new_round()
        self.assertEqual(self.app.round_number, 2)
        self.assertFalse(self.app.game.game_over)
        self.assertEqual(self.app.game.starting_player, "O")


if __name__ == "__main__":
    unittest.main()
