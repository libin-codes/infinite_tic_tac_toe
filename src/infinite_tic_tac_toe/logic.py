"""Core game logic for Infinite Tic-Tac-Toe."""

from typing import List, Optional, Tuple, Dict, Any


class InfiniteTicTacToeLogic:
    """Manages the board state and rules for Infinite Tic-Tac-Toe.
    
    Each player ('X' and 'O') may have at most MAX_PIECES (3) on the board.
    When a player has 3 marks and makes a move, their oldest mark vanishes,
    and their new mark is added.
    """

    MAX_PIECES = 3
    WINNING_COMBINATIONS = [
        # Rows
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        # Columns
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        # Diagonals
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)],
    ]

    def __init__(self, starting_player: str = "X") -> None:
        self.starting_player = starting_player
        self.board: List[List[Optional[str]]] = [[None for _ in range(3)] for _ in range(3)]
        self.player_moves: Dict[str, List[Tuple[int, int]]] = {"X": [], "O": []}
        self.current_player: str = starting_player
        self.winner: Optional[str] = None
        self.winning_line: Optional[List[Tuple[int, int]]] = None
        self.game_over: bool = False

    def reset(self, alternate_starting: bool = False) -> None:
        """Reset the board for a new round."""
        if alternate_starting:
            self.starting_player = "O" if self.starting_player == "X" else "X"
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.player_moves = {"X": [], "O": []}
        self.current_player = self.starting_player
        self.winner = None
        self.winning_line = None
        self.game_over = False

    @property
    def is_empty(self) -> bool:
        """Return True if no marks are currently on the board."""
        return not self.player_moves["X"] and not self.player_moves["O"]

    def is_valid_move(self, r: int, c: int) -> bool:
        """Check if placing a mark at (r, c) is a valid move."""
        if self.game_over:
            return False
        if not (0 <= r < 3 and 0 <= c < 3):
            return False
        return self.board[r][c] is None

    def get_expiring_piece(self, player: Optional[str] = None) -> Optional[Tuple[int, int]]:
        """Return the coordinate of the piece that will vanish next for the given player."""
        target_player = player or self.current_player
        moves = self.player_moves[target_player]
        if len(moves) >= self.MAX_PIECES:
            return moves[0]
        return None

    def get_piece_info(self, r: int, c: int) -> Optional[Dict[str, Any]]:
        """Return player and age metadata for a cell (r, c).
        
        age: 1 (oldest, vanishes next if 3 on board), 2 (middle), 3 (newest).
        """
        player = self.board[r][c]
        if not player:
            return None
        moves = self.player_moves[player]
        try:
            # 0-indexed in queue: 0 is oldest, len-1 is newest
            idx = moves.index((r, c))
            # Normalized age relative to total pieces (1..3)
            # If 3 pieces: idx 0 -> age 1, idx 1 -> age 2, idx 2 -> age 3
            # If 2 pieces: idx 0 -> age 2, idx 1 -> age 3
            # If 1 piece:  idx 0 -> age 3
            age = (self.MAX_PIECES - len(moves)) + idx + 1
            is_next_to_vanish = (idx == 0 and len(moves) == self.MAX_PIECES)
            return {
                "player": player,
                "order_idx": idx,
                "total_pieces": len(moves),
                "age": age,
                "is_next_to_vanish": is_next_to_vanish,
            }
        except ValueError:
            return None

    def make_move(self, r: int, c: int) -> Dict[str, Any]:
        """Make a move at (r, c).
        
        Returns a dict summarizing the outcome of the move.
        """
        if not self.is_valid_move(r, c):
            return {"success": False, "reason": "Invalid move"}

        player = self.current_player
        vanished_piece: Optional[Tuple[int, int]] = None

        # Remove oldest piece if player already has MAX_PIECES
        if len(self.player_moves[player]) >= self.MAX_PIECES:
            vanished_piece = self.player_moves[player].pop(0)
            self.board[vanished_piece[0]][vanished_piece[1]] = None

        # Place new piece
        self.board[r][c] = player
        self.player_moves[player].append((r, c))

        # Check win condition for current player
        win_combo = self._check_win(player)
        if win_combo is not None:
            self.winner = player
            self.winning_line = win_combo
            self.game_over = True
        else:
            self.current_player = "O" if player == "X" else "X"

        return {
            "success": True,
            "player": player,
            "placed": (r, c),
            "vanished": vanished_piece,
            "winner": self.winner,
            "winning_line": self.winning_line,
            "next_player": self.current_player,
            "game_over": self.game_over,
        }

    def _check_win(self, player: str) -> Optional[List[Tuple[int, int]]]:
        """Check if the given player has formed a winning line."""
        for combo in self.WINNING_COMBINATIONS:
            if all(self.board[r][c] == player for r, c in combo):
                return combo
        return None
