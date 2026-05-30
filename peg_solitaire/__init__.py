"""Triangle Peg Solitaire game package."""

from .game import (
    MIN_ROWS,
    InvalidMove,
    Move,
    ScoreResult,
    TrianglePegSolitaire,
    score_board,
)

__all__ = [
    "MIN_ROWS",
    "InvalidMove",
    "Move",
    "ScoreResult",
    "TrianglePegSolitaire",
    "score_board",
]
