import tempfile
import unittest
from pathlib import Path

from peg_solitaire.storage import GameStats, load_stats, record_game, save_stats


class StorageTests(unittest.TestCase):
    def test_load_missing_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            stats = load_stats(Path(directory) / "missing.json")

        self.assertEqual(stats.games_played, 0)
        self.assertEqual(stats.wins, 0)
        self.assertFalse(stats.tutorial_dismissed)
        self.assertTrue(stats.sound_enabled)

    def test_save_and_load_round_trips_settings_and_row_bests(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.json"
            stats = GameStats(tutorial_dismissed=True, sound_enabled=False)
            record_game(stats, rows=5, score=25, pegs_remaining=2, is_win=False)
            save_stats(stats, path)

            loaded = load_stats(path)

        self.assertTrue(loaded.tutorial_dismissed)
        self.assertFalse(loaded.sound_enabled)
        self.assertEqual(loaded.games_played, 1)
        self.assertEqual(loaded.best_by_rows["5"].best_score, 25)

    def test_corrupted_json_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.json"
            path.write_text("{not-json", encoding="utf-8")

            stats = load_stats(path)

        self.assertEqual(stats, GameStats())

    def test_record_game_tracks_wins_and_records(self):
        stats = GameStats()

        first = record_game(
            stats,
            rows=5,
            score=25,
            pegs_remaining=2,
            is_win=False,
        )
        second = record_game(
            stats,
            rows=5,
            score=100,
            pegs_remaining=1,
            is_win=True,
        )

        self.assertTrue(first.score_record)
        self.assertTrue(first.pegs_record)
        self.assertTrue(second.is_win)
        self.assertTrue(second.score_record)
        self.assertTrue(second.pegs_record)
        self.assertEqual(stats.games_played, 2)
        self.assertEqual(stats.wins, 1)
        self.assertEqual(stats.best_score, 100)
        self.assertEqual(stats.fewest_pegs_remaining, 1)
        self.assertEqual(stats.best_by_rows["5"].wins, 1)

    def test_tutorial_dismissed_flag_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.json"
            stats = GameStats()
            stats.tutorial_dismissed = True
            save_stats(stats, path)

            loaded = load_stats(path)

        self.assertTrue(loaded.tutorial_dismissed)


if __name__ == "__main__":
    unittest.main()
