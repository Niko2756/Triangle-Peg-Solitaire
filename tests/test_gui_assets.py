import unittest

from peg_solitaire.gui import GAME_CURSOR, WOOD_TEXTURE


class GuiAssetTests(unittest.TestCase):
    def test_wood_texture_is_available_for_gui(self):
        self.assertTrue(WOOD_TEXTURE.exists())

    def test_game_cursor_is_available_for_gui(self):
        self.assertTrue(GAME_CURSOR.exists())


if __name__ == "__main__":
    unittest.main()
