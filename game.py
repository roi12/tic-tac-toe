"""PyQt5 implementation of a Tic-Tac-Toe game with human and AI modes.

The module exposes a :class:`TicTacToeGame` widget that can be launched
directly (``python game.py``).  The GUI consists of:

* A 3×3 grid of buttons representing the board.
* A status label that communicates whose turn it is or the game result.
* Controls to switch between Player vs. Player and Player vs. AI modes.
* Controls to select the AI difficulty (Easy/Medium/Hard) and to reset the game.

The AI implementation supports three difficulty levels:

* ``Easy`` – chooses a random available move.
* ``Medium`` – uses a depth-limited minimax search.
* ``Hard`` – uses a full minimax search to guarantee optimal play.

Both the GUI flow and the decision logic are documented throughout the
implementation to provide clarity on how user interactions translate
to updates on the board and how the AI determines its moves.
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass
class GameConfig:
    """Container for configuration that influences AI behaviour."""

    mode: str = "ai"  # Either "pvp" or "ai".
    difficulty: str = "Medium"  # Easy, Medium, Hard.


class TicTacToeGame(QMainWindow):
    """Main window hosting the Tic-Tac-Toe board and controls."""

    HUMAN_MARK = "X"
    AI_MARK = "O"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PyQt Tic-Tac-Toe")

        # Internal state used to track game progress.
        self.board: List[Optional[str]] = [None] * 9
        self.current_player: str = self.HUMAN_MARK
        self.game_over: bool = False
        self.config = GameConfig()

        # Widgets stored for later updates.
        self.buttons: List[QPushButton] = []
        self.status_label = QLabel()
        self.mode_buttons: dict[str, QPushButton] = {}
        self.difficulty_combo = QComboBox()

        self._build_ui()
        self._update_status()

    # ------------------------------------------------------------------
    # UI setup helpers
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Create and arrange the widgets composing the interface."""

        container = QWidget()
        layout = QVBoxLayout(container)

        layout.addWidget(self._build_mode_controls())
        layout.addWidget(self._build_board())
        layout.addWidget(self._build_status_bar())

        self.setCentralWidget(container)

    def _build_mode_controls(self) -> QWidget:
        """Create controls for selecting the game mode and AI difficulty."""

        controls = QGroupBox("Mode & Difficulty")
        controls_layout = QVBoxLayout(controls)

        # Mode selection buttons make it explicit which mode is active.
        mode_layout = QHBoxLayout()
        for mode_key, label in (("pvp", "Player vs Player"), ("ai", "Player vs AI")):
            button = QPushButton(label)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, m=mode_key: self.set_mode(m))
            self.mode_buttons[mode_key] = button
            mode_layout.addWidget(button)
        controls_layout.addLayout(mode_layout)

        # Difficulty options control the intelligence of the AI opponent.
        difficulty_layout = QHBoxLayout()
        difficulty_layout.addWidget(QLabel("AI Difficulty:"))
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        self.difficulty_combo.currentTextChanged.connect(self.set_difficulty)
        difficulty_layout.addWidget(self.difficulty_combo)

        reset_button = QPushButton("Reset Game")
        reset_button.clicked.connect(self.reset_board)
        difficulty_layout.addWidget(reset_button)

        controls_layout.addLayout(difficulty_layout)

        # Initialise the UI to reflect the default configuration.
        self._update_mode_buttons()
        self.difficulty_combo.setCurrentText(self.config.difficulty)

        return controls

    def _build_board(self) -> QWidget:
        """Create the 3×3 grid of buttons representing the board."""

        board_widget = QGroupBox("Board")
        grid_layout = QGridLayout(board_widget)

        for index in range(9):
            button = QPushButton(" ")
            button.setFixedSize(100, 100)
            font = button.font()
            font.setPointSize(24)
            button.setFont(font)
            button.clicked.connect(lambda _checked, idx=index: self.handle_move(idx))
            row, col = divmod(index, 3)
            grid_layout.addWidget(button, row, col)
            self.buttons.append(button)

        return board_widget

    def _build_status_bar(self) -> QWidget:
        """Create the status display shown below the board."""

        status_widget = QGroupBox("Status")
        layout = QHBoxLayout(status_widget)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        return status_widget

    # ------------------------------------------------------------------
    # Event handlers and UI updates
    # ------------------------------------------------------------------
    def set_mode(self, mode: str) -> None:
        """Update the game mode and reset the board if necessary."""

        if mode not in {"pvp", "ai"}:
            return
        if self.config.mode != mode:
            self.config.mode = mode
            self.reset_board()
        self._update_mode_buttons()

    def set_difficulty(self, difficulty: str) -> None:
        """Update the AI difficulty level."""

        if difficulty not in {"Easy", "Medium", "Hard"}:
            return
        self.config.difficulty = difficulty
        # Resetting gives the AI a fresh game whenever difficulty changes.
        self.reset_board()

    def _update_mode_buttons(self) -> None:
        for mode, button in self.mode_buttons.items():
            button.setChecked(mode == self.config.mode)

    def _update_status(self, message: Optional[str] = None) -> None:
        """Refresh the status label with contextual information."""

        if message:
            self.status_label.setText(message)
            return

        if self.game_over:
            winner = self.check_winner(self.board)
            if winner == "Draw":
                self.status_label.setText("The game is a draw.")
            else:
                self.status_label.setText(f"{winner} wins!")
        else:
            if self.config.mode == "ai" and self.current_player == self.AI_MARK:
                self.status_label.setText("AI is thinking...")
            else:
                self.status_label.setText(f"{self.current_player}'s turn")

    def reset_board(self) -> None:
        """Clear the board and reset internal state."""

        self.board = [None] * 9
        self.current_player = self.HUMAN_MARK
        self.game_over = False
        for button in self.buttons:
            button.setText(" ")
            button.setEnabled(True)
        self._update_status()

        # If AI mode starts with the AI, let it play immediately.
        if self.config.mode == "ai" and self.current_player == self.AI_MARK:
            self._trigger_ai_turn()

    def handle_move(self, index: int) -> None:
        """Handle clicks on board buttons and advance the game state."""

        if self.game_over or self.board[index] is not None:
            return

        # Update the model and mirror the change in the UI.
        self.board[index] = self.current_player
        self.buttons[index].setText(self.current_player)
        self.buttons[index].setEnabled(False)

        if self._check_game_end():
            return

        # Switch turns and, if appropriate, trigger the AI immediately.
        self.current_player = self.AI_MARK if self.current_player == self.HUMAN_MARK else self.HUMAN_MARK
        self._update_status()

        if self.config.mode == "ai" and self.current_player == self.AI_MARK:
            self._trigger_ai_turn()

    def _trigger_ai_turn(self) -> None:
        """Perform an AI move according to the configured difficulty."""

        QApplication.processEvents()

        move = self._choose_ai_move()
        if move is None:
            return
        self.handle_move(move)

    # ------------------------------------------------------------------
    # Game state helpers
    # ------------------------------------------------------------------
    @staticmethod
    def available_moves(board: List[Optional[str]]) -> List[int]:
        return [idx for idx, value in enumerate(board) if value is None]

    @staticmethod
    def check_winner(board: List[Optional[str]]) -> Optional[str]:
        """Return the winner ("X"/"O"), "Draw" or ``None`` if undecided."""

        winning_lines = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6),
        ]
        for a, b, c in winning_lines:
            if board[a] and board[a] == board[b] == board[c]:
                return board[a]
        if all(value is not None for value in board):
            return "Draw"
        return None

    def _check_game_end(self) -> bool:
        """Evaluate whether the game has been won or drawn."""

        result = self.check_winner(self.board)
        if result:
            self.game_over = True
            for button in self.buttons:
                button.setEnabled(False)
            self._update_status()
            # Provide a modal prompt so the user can immediately restart.
            QMessageBox.information(self, "Game Over", self.status_label.text())
            return True
        return False

    # ------------------------------------------------------------------
    # AI logic
    # ------------------------------------------------------------------
    def _choose_ai_move(self) -> Optional[int]:
        """Dispatch to the AI strategy configured for the current difficulty."""

        available = self.available_moves(self.board)
        if not available:
            return None

        if self.config.difficulty == "Easy":
            return random.choice(available)

        if self.config.difficulty == "Medium":
            _, move = self._minimax(self.board, is_maximizing=True, depth_limit=3)
            return move if move is not None else random.choice(available)

        # Hard difficulty defaults to a full minimax search.
        _, move = self._minimax(self.board, is_maximizing=True, depth_limit=None)
        return move if move is not None else random.choice(available)

    def _minimax(
        self,
        board: List[Optional[str]],
        *,
        is_maximizing: bool,
        depth_limit: Optional[int],
        depth: int = 0,
    ) -> Tuple[float, Optional[int]]:
        """Perform a minimax search.

        Parameters
        ----------
        board:
            Snapshot of the board for which the optimal move is sought.
        is_maximizing:
            ``True`` when it is the AI's turn; ``False`` for the human.
        depth_limit:
            Maximum depth explored (``None`` for unlimited).
        depth:
            Current recursion depth used for limit enforcement and for
            slight score adjustments that favour quicker victories.

        Returns
        -------
        tuple
            ``(score, move)`` representing the outcome value and the index of
            the best move.  Scores are positive for AI-favourable states and
            negative for human-favourable states.
        """

        result = self.check_winner(board)
        if result == self.AI_MARK:
            return 10 - depth, None
        if result == self.HUMAN_MARK:
            return depth - 10, None
        if result == "Draw":
            return 0, None

        if depth_limit is not None and depth >= depth_limit:
            # At the depth limit, evaluate the board heuristically.  Here we
            # simply return neutral (0), but the depth-based adjustments above
            # already provide a bias toward swift wins and slow losses.
            return 0, None

        best_move: Optional[int] = None
        if is_maximizing:
            best_score = -math.inf
            mark = self.AI_MARK
        else:
            best_score = math.inf
            mark = self.HUMAN_MARK

        for move in self.available_moves(board):
            board[move] = mark
            score, _ = self._minimax(
                board,
                is_maximizing=not is_maximizing,
                depth_limit=depth_limit,
                depth=depth + 1,
            )
            board[move] = None

            if is_maximizing:
                if score > best_score:
                    best_score, best_move = score, move
            else:
                if score < best_score:
                    best_score, best_move = score, move

        return best_score, best_move


def main() -> int:
    """Instantiate the application and run the Qt event loop.

    Returning an integer exit code makes it easier to integrate the
    application with scripts or tests that launch the GUI.
    """

    app = QApplication(sys.argv)
    game = TicTacToeGame()
    game.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
