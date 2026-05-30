import unittest

from peg_solitaire.game import InvalidMove, Move, TrianglePegSolitaire, score_board


class TrianglePegSolitaireTests(unittest.TestCase):
    def test_board_indexes_match_original_triangle_layout(self):
        game = TrianglePegSolitaire(rows=5)

        self.assertEqual(game.total_holes, 15)
        self.assertEqual(game.position_for_index(0), (0, 0))
        self.assertEqual(game.position_for_index(1), (0, 1))
        self.assertEqual(game.position_for_index(2), (1, 1))
        self.assertEqual(game.position_for_index(14), (4, 4))
        self.assertEqual(game.rows_as_indexes()[2], [3, 4, 5])

    def test_board_requires_at_least_four_rows(self):
        with self.assertRaises(ValueError):
            TrianglePegSolitaire(rows=3)

    def test_starting_peg_uses_zero_based_range(self):
        game = TrianglePegSolitaire(rows=5)

        with self.assertRaises(IndexError):
            game.remove_starting_peg(game.total_holes)

    def test_possible_moves_after_removing_top_peg(self):
        game = TrianglePegSolitaire(rows=5)
        game.remove_starting_peg(0)

        self.assertEqual(
            game.possible_moves(),
            [Move(start=3, over=1, end=0), Move(start=5, over=2, end=0)],
        )

    def test_apply_move_updates_start_middle_and_end(self):
        game = TrianglePegSolitaire(rows=5)
        game.remove_starting_peg(0)

        move = game.apply_move(3, 0)

        self.assertEqual(move, Move(start=3, over=1, end=0))
        self.assertEqual(game.pegs[0], 1)
        self.assertEqual(game.pegs[1], 0)
        self.assertEqual(game.pegs[3], 0)
        self.assertEqual(game.remaining_pegs, 13)

    def test_invalid_move_reports_bad_index_without_crashing(self):
        game = TrianglePegSolitaire(rows=5)
        game.remove_starting_peg(0)

        with self.assertRaises(InvalidMove):
            game.validate_move(game.total_holes, 0)

    def test_score_for_returning_to_starting_hole(self):
        pegs = [0] * 10
        pegs[0] = 1

        score = score_board(pegs, starting_empty=0)

        self.assertEqual(score.points, 100)
        self.assertTrue(score.is_win)

    def test_score_for_one_remaining_peg_elsewhere(self):
        pegs = [0] * 10
        pegs[4] = 1

        score = score_board(pegs, starting_empty=0)

        self.assertEqual(score.points, 50)
        self.assertTrue(score.is_win)


if __name__ == "__main__":
    unittest.main()
