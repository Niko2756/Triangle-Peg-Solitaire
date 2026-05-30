import unittest

from peg_solitaire.gui import WOOD_TEXTURE


class GuiAssetTests(unittest.TestCase):
    def test_wood_texture_is_available_for_gui(self):
        self.assertTrue(WOOD_TEXTURE.exists())


if __name__ == "__main__":
    unittest.main()
