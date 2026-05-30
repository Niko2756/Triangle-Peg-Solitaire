"""Core Triangle Peg Solitaire rules.

This module intentionally has no console input or output. The GUI can import
these classes directly and make moves without inheriting the text UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field


MIN_ROWS = 4
JUMP_DIRECTIONS = (
    (0, 2),
    (2, 2),
    (2, 0),
    (-2, 0),
    (-2, -2),
    (0, -2),
)


class InvalidMove(ValueError):
    """Raised when a requested move does not follow peg solitaire rules."""


@dataclass(frozen=True)
class Move:
    """A complete jump from one peg, over the middle peg, into an empty hole."""

    start: int
    over: int
    end: int


@dataclass(frozen=True)
class ScoreResult:
    """Score and end-of-round message for a finished board."""

    points: int
    title: str
    message: str
    is_win: bool


@dataclass
class TrianglePegSolitaire:
    """Playable triangular peg solitaire board."""

    rows: int = 5
    starting_empty: int | None = None
    pegs: list[int] = field(init=False)
    _positions: list[tuple[int, int]] = field(init=False, repr=False)
    _index_by_position: dict[tuple[int, int], int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.rows < MIN_ROWS:
            raise ValueError(f"Triangle Peg Solitaire needs at least {MIN_ROWS} rows.")

        self._positions = [
            (column, row)
            for row in range(self.rows)
            for column in range(row + 1)
        ]
        self._index_by_position = {
            position: index for index, position in enumerate(self._positions)
        }
        self.pegs = [1] * len(self._positions)

        starting_empty = self.starting_empty
        self.starting_empty = None
        if starting_empty is not None:
            self.remove_starting_peg(starting_empty)

    @classmethod
    def from_pegs(
        cls,
        rows: int,
        pegs: list[int],
        starting_empty: int | None = None,
    ) -> "TrianglePegSolitaire":
        game = cls(rows=rows)
        if len(pegs) != game.total_holes:
            raise ValueError(
                f"Expected {game.total_holes} peg values for a {rows}-row board."
            )
        if any(peg not in (0, 1) for peg in pegs):
            raise ValueError("Peg values must be 0 for empty or 1 for filled.")
        if starting_empty is not None:
            game.require_index(starting_empty)
        game.pegs = list(pegs)
        game.starting_empty = starting_empty
        return game

    @property
    def total_holes(self) -> int:
        return len(self.pegs)

    @property
    def remaining_pegs(self) -> int:
        return sum(self.pegs)

    def contains_index(self, index: int) -> bool:
        return 0 <= index < self.total_holes

    def require_index(self, index: int) -> None:
        if not self.contains_index(index):
            raise IndexError(
                f"Please enter a peg between 0 and {self.total_holes - 1}."
            )

    def position_for_index(self, index: int) -> tuple[int, int]:
        self.require_index(index)
        return self._positions[index]

    def index_for_position(self, column: int, row: int) -> int | None:
        return self._index_by_position.get((column, row))

    def rows_as_indexes(self) -> list[list[int]]:
        rows: list[list[int]] = []
        next_index = 0
        for row in range(self.rows):
            row_length = row + 1
            rows.append(list(range(next_index, next_index + row_length)))
            next_index += row_length
        return rows

    def rows_as_values(self) -> list[list[int]]:
        return [[self.pegs[index] for index in row] for row in self.rows_as_indexes()]

    def remove_starting_peg(self, index: int) -> None:
        self.require_index(index)
        if self.starting_empty is not None:
            raise ValueError("The starting peg has already been removed.")
        self.pegs[index] = 0
        self.starting_empty = index

    def middle_peg_index(self, start: int, end: int) -> int | None:
        self.require_index(start)
        self.require_index(end)
        start_column, start_row = self.position_for_index(start)
        end_column, end_row = self.position_for_index(end)
        column_delta = end_column - start_column
        row_delta = end_row - start_row

        if (column_delta, row_delta) not in JUMP_DIRECTIONS:
            return None

        middle_position = (
            start_column + (column_delta // 2),
            start_row + (row_delta // 2),
        )
        return self._index_by_position.get(middle_position)

    def validate_move(self, start: int, end: int) -> Move:
        try:
            self.require_index(start)
            self.require_index(end)
        except IndexError as exc:
            raise InvalidMove(str(exc)) from exc

        if self.pegs[start] != 1:
            raise InvalidMove("There is no peg there. Pick a hole with a peg.")
        if self.pegs[end] != 0:
            raise InvalidMove("Please pick an empty hole for the landing spot.")

        try:
            middle = self.middle_peg_index(start, end)
        except IndexError as exc:
            raise InvalidMove(str(exc)) from exc

        if middle is None:
            raise InvalidMove("That move is not permitted by the triangle.")
        if self.pegs[middle] != 1:
            raise InvalidMove("The peg you would jump over is already gone.")

        return Move(start=start, over=middle, end=end)

    def apply_move(self, start: int, end: int) -> Move:
        move = self.validate_move(start, end)
        self.pegs[move.start] = 0
        self.pegs[move.over] = 0
        self.pegs[move.end] = 1
        return move

    def possible_moves(self) -> list[Move]:
        moves: list[Move] = []
        for start, has_peg in enumerate(self.pegs):
            if has_peg != 1:
                continue

            start_column, start_row = self.position_for_index(start)
            for column_delta, row_delta in JUMP_DIRECTIONS:
                over = self.index_for_position(
                    start_column + (column_delta // 2),
                    start_row + (row_delta // 2),
                )
                end = self.index_for_position(
                    start_column + column_delta,
                    start_row + row_delta,
                )
                if over is None or end is None:
                    continue
                if self.pegs[over] == 1 and self.pegs[end] == 0:
                    moves.append(Move(start=start, over=over, end=end))
        return moves

    def possible_move_count(self) -> int:
        return len(self.possible_moves())

    def has_moves(self) -> bool:
        return self.possible_move_count() > 0

    def is_finished(self) -> bool:
        return not self.has_moves()


def score_board(pegs: list[int], starting_empty: int | None) -> ScoreResult:
    remaining = sum(pegs)
    total = len(pegs)
    remaining_percent = int((remaining / total) * 100) if total else 0

    if remaining == 1 and starting_empty is not None and pegs[starting_empty] == 1:
        return ScoreResult(
            points=100,
            title="WOW, you are brilliant!",
            message=(
                "That was outstandingly astonishing. The final peg returned "
                "to the first empty spot like it planned the whole thing."
            ),
            is_win=True,
        )
    if remaining == 1:
        return ScoreResult(
            points=50,
            title="Fantastic, you are very smart.",
            message=(
                "You win, but what you have won is for you to decide and "
                "for the rest of us to find out."
            ),
            is_win=True,
        )
    if remaining == 2:
        return ScoreResult(
            points=25,
            title="Awesome, you are above average!",
            message="The board is trying to act casual about it, but it noticed.",
            is_win=False,
        )
    if remaining == 3:
        return ScoreResult(
            points=10,
            title="Nice, just so-so, but still nice.",
            message="Respectable. Not legendary, but respectable.",
            is_win=False,
        )
    if remaining > 3 and remaining_percent > 51:
        return ScoreResult(
            points=200,
            title="Amazing, you are a genius!",
            message=(
                "You kept more than half the pegs on the board with no moves "
                "left. That is either strategy or suspiciously advanced math."
            ),
            is_win=False,
        )

    return ScoreResult(
        points=0,
        title="GAME OVER.",
        message=(
            "You get no points because that was okay, but not exactly "
            "museum-quality strategy."
        ),
        is_win=False,
    )
