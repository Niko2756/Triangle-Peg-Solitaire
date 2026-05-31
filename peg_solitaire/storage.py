"""Persistent stats and settings for the Triangle Peg Solitaire GUI."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_STATS_PATH = Path.home() / ".triangle_peg_solitaire" / "stats.json"
ANIMATION_SPEEDS = ("relaxed", "normal", "quick")
CURSOR_MODES = ("auto", "system")


@dataclass
class RowBest:
    """Best results for one board size."""

    games_played: int = 0
    wins: int = 0
    best_score: int = 0
    fewest_pegs_remaining: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RowBest":
        return cls(
            games_played=max(0, _as_int(data.get("games_played"), 0)),
            wins=max(0, _as_int(data.get("wins"), 0)),
            best_score=max(0, _as_int(data.get("best_score"), 0)),
            fewest_pegs_remaining=_as_optional_int(data.get("fewest_pegs_remaining")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "games_played": self.games_played,
            "wins": self.wins,
            "best_score": self.best_score,
            "fewest_pegs_remaining": self.fewest_pegs_remaining,
        }


@dataclass
class GameStats:
    """Resume-friendly local game stats plus small GUI settings."""

    games_played: int = 0
    wins: int = 0
    best_score: int = 0
    fewest_pegs_remaining: int | None = None
    tutorial_dismissed: bool = False
    sound_enabled: bool = True
    animation_speed: str = "normal"
    cursor_mode: str = "auto"
    best_by_rows: dict[str, RowBest] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameStats":
        animation_speed = str(data.get("animation_speed", "normal"))
        if animation_speed not in ANIMATION_SPEEDS:
            animation_speed = "normal"

        cursor_mode = str(data.get("cursor_mode", "auto"))
        if cursor_mode not in CURSOR_MODES:
            cursor_mode = "auto"

        raw_rows = data.get("best_by_rows")
        best_by_rows: dict[str, RowBest] = {}
        if isinstance(raw_rows, dict):
            for key, value in raw_rows.items():
                if isinstance(value, dict):
                    best_by_rows[str(key)] = RowBest.from_dict(value)

        return cls(
            games_played=max(0, _as_int(data.get("games_played"), 0)),
            wins=max(0, _as_int(data.get("wins"), 0)),
            best_score=max(0, _as_int(data.get("best_score"), 0)),
            fewest_pegs_remaining=_as_optional_int(data.get("fewest_pegs_remaining")),
            tutorial_dismissed=bool(data.get("tutorial_dismissed", False)),
            sound_enabled=bool(data.get("sound_enabled", True)),
            animation_speed=animation_speed,
            cursor_mode=cursor_mode,
            best_by_rows=best_by_rows,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "games_played": self.games_played,
            "wins": self.wins,
            "best_score": self.best_score,
            "fewest_pegs_remaining": self.fewest_pegs_remaining,
            "tutorial_dismissed": self.tutorial_dismissed,
            "sound_enabled": self.sound_enabled,
            "animation_speed": self.animation_speed,
            "cursor_mode": self.cursor_mode,
            "best_by_rows": {
                key: value.to_dict() for key, value in sorted(self.best_by_rows.items())
            },
        }


@dataclass(frozen=True)
class StatsUpdate:
    """Details about what changed after a completed round."""

    games_played: int
    wins: int
    is_win: bool
    score_record: bool
    pegs_record: bool
    row_score_record: bool
    row_pegs_record: bool

    @property
    def has_record(self) -> bool:
        return (
            self.score_record
            or self.pegs_record
            or self.row_score_record
            or self.row_pegs_record
        )


def load_stats(path: Path = DEFAULT_STATS_PATH) -> GameStats:
    """Load stats, returning defaults when the file is missing or invalid."""

    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return GameStats()
    if not isinstance(raw_data, dict):
        return GameStats()
    return GameStats.from_dict(raw_data)


def save_stats(stats: GameStats, path: Path = DEFAULT_STATS_PATH) -> None:
    """Persist stats atomically enough for a tiny local JSON settings file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(stats.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def record_game(
    stats: GameStats,
    *,
    rows: int,
    score: int,
    pegs_remaining: int,
    is_win: bool,
) -> StatsUpdate:
    """Update cumulative and per-row stats after one completed round."""

    score = max(0, score)
    pegs_remaining = max(0, pegs_remaining)
    row_key = str(rows)
    row_stats = stats.best_by_rows.setdefault(row_key, RowBest())

    old_best_score = stats.best_score
    old_fewest_pegs = stats.fewest_pegs_remaining
    old_row_best_score = row_stats.best_score
    old_row_fewest_pegs = row_stats.fewest_pegs_remaining

    stats.games_played += 1
    row_stats.games_played += 1
    if is_win:
        stats.wins += 1
        row_stats.wins += 1

    stats.best_score = max(stats.best_score, score)
    row_stats.best_score = max(row_stats.best_score, score)
    if stats.fewest_pegs_remaining is None:
        stats.fewest_pegs_remaining = pegs_remaining
    else:
        stats.fewest_pegs_remaining = min(stats.fewest_pegs_remaining, pegs_remaining)
    if row_stats.fewest_pegs_remaining is None:
        row_stats.fewest_pegs_remaining = pegs_remaining
    else:
        row_stats.fewest_pegs_remaining = min(
            row_stats.fewest_pegs_remaining,
            pegs_remaining,
        )

    return StatsUpdate(
        games_played=stats.games_played,
        wins=stats.wins,
        is_win=is_win,
        score_record=score > old_best_score,
        pegs_record=old_fewest_pegs is None or pegs_remaining < old_fewest_pegs,
        row_score_record=score > old_row_best_score,
        row_pegs_record=(
            old_row_fewest_pegs is None or pegs_remaining < old_row_fewest_pegs
        ),
    )


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None
