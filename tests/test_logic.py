import unittest

from infinite_tic_tac_toe.models import GameSession, InfiniteTicTacToeLogic


class TestInfiniteTicTacToeLogic(unittest.TestCase):
    def setUp(self):
        self.game = InfiniteTicTacToeLogic()

    def test_initial_state(self):
        self.assertEqual(self.game.current_player, "X")
        self.assertIsNone(self.game.winner)
        self.assertFalse(self.game.game_over)
        self.assertTrue(self.game.is_empty)
        for r in range(3):
            for c in range(3):
                self.assertIsNone(self.game.board[r][c])

    def test_is_empty_behavior(self):
        self.assertTrue(self.game.is_empty)
        self.game.make_move(0, 0)
        self.assertFalse(self.game.is_empty)
        self.game.reset()
        self.assertTrue(self.game.is_empty)

    def test_normal_placement(self):
        res = self.game.make_move(0, 0)
        self.assertTrue(res["success"])
        self.assertEqual(self.game.board[0][0], "X")
        self.assertEqual(self.game.current_player, "O")
        self.assertIsNone(res["vanished"])

    def test_queue_and_vanishing(self):
        # Move 1: X at (0, 0)
        self.game.make_move(0, 0)
        # Move 2: O at (1, 0)
        self.game.make_move(1, 0)
        # Move 3: X at (0, 1)
        self.game.make_move(0, 1)
        # Move 4: O at (1, 1)
        self.game.make_move(1, 1)
        # Move 5: X at (2, 0) -> X now has (0,0), (0,1), (2,0) (3 pieces)
        self.game.make_move(2, 0)
        # Move 6: O at (2, 1) -> O now has (1,0), (1,1), (2,1) (3 pieces)
        self.game.make_move(2, 1)

        self.assertEqual(len(self.game.player_moves["X"]), 3)
        self.assertEqual(len(self.game.player_moves["O"]), 3)

        # X's next move is 4th move. Oldest is (0, 0).
        self.assertEqual(self.game.get_expiring_piece("X"), (0, 0))

        # Move 7: X moves to (0, 2)
        res = self.game.make_move(0, 2)
        self.assertTrue(res["success"])
        self.assertEqual(res["vanished"], (0, 0))
        # (0, 0) should now be empty!
        self.assertIsNone(self.game.board[0][0])
        # X's moves should be (0,1), (2,0), (0,2)
        self.assertEqual(self.game.player_moves["X"], [(0, 1), (2, 0), (0, 2)])

    def test_win_condition(self):
        # X: (0,0), O: (1,0), X: (0,1), O: (1,1), X: (0,2) -> X wins row 0
        self.game.make_move(0, 0) # X
        self.game.make_move(1, 0) # O
        self.game.make_move(0, 1) # X
        self.game.make_move(1, 1) # O
        res = self.game.make_move(0, 2) # X wins
        self.assertTrue(res["game_over"])
        self.assertEqual(res["winner"], "X")
        self.assertEqual(self.game.winner, "X")
        self.assertEqual(res["winning_line"], [(0, 0), (0, 1), (0, 2)])

    def test_win_after_piece_vanishes(self):
        # Ensure a win happens when placing 4th piece which completes 3-in-a-row
        # X moves: (2,2), O: (0,1), X: (0,0), O: (1,1), X: (0,2), O: (2,1)
        # X pieces: (2,2) [oldest], (0,0), (0,2)
        # X places (0,1) -> (2,2) vanishes! Remaining X: (0,0), (0,2), (0,1) -> row 0 forms!
        self.game.make_move(2, 2) # X (oldest)
        self.game.make_move(1, 0) # O
        self.game.make_move(0, 0) # X
        self.game.make_move(1, 1) # O
        self.game.make_move(0, 2) # X
        self.game.make_move(2, 0) # O

        # X now has (2,2), (0,0), (0,2). Placing at (0,1) should vacate (2,2) and win row 0!
        res = self.game.make_move(0, 1)
        self.assertTrue(res["success"])
        self.assertEqual(res["vanished"], (2, 2))
        self.assertTrue(res["game_over"])
        self.assertEqual(res["winner"], "X")
        self.assertIn((0, 0), res["winning_line"])
        self.assertIn((0, 1), res["winning_line"])
        self.assertIn((0, 2), res["winning_line"])


class TestGameSession(unittest.TestCase):
    def setUp(self):
        self.session = GameSession()

    def test_initial_session(self):
        self.assertEqual(self.session.round_number, 1)
        self.assertEqual(self.session.scores, {"X": 0, "O": 0})
        self.assertFalse(self.session.has_progress)

    def test_record_win_and_progress(self):
        self.session.record_win("X")
        self.assertEqual(self.session.scores["X"], 1)
        self.assertEqual(self.session.scores["O"], 0)
        self.assertTrue(self.session.has_progress)

    def test_next_round(self):
        r = self.session.next_round()
        self.assertEqual(r, 2)
        self.assertEqual(self.session.round_number, 2)
        self.assertTrue(self.session.has_progress)

    def test_reset_all(self):
        self.session.record_win("O")
        self.session.next_round()
        self.session.reset_all()
        self.assertEqual(self.session.round_number, 1)
        self.assertEqual(self.session.scores, {"X": 0, "O": 0})
        self.assertFalse(self.session.has_progress)


if __name__ == "__main__":
    unittest.main()
