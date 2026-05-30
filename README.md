# Triangle Peg Solitaire

A Python version of Triangle Peg Solitaire, originally written as a console game
with only the Python standard library.

The project now includes a playable desktop GUI. It keeps the funny, personal
console voice while separating the reusable game rules from the text prompts, so
the same rule engine can power the console game and the graphical game.

## Features

- Playable Tkinter GUI with a wooden board-game panel, blue guide lines, recessed
  holes, and white pegs.
- Console version still works through the original filename.
- Row count can be changed from 4 to 10 in the GUI.
- New Game, Undo, Hint, score, remaining peg count, and available move count.
- Core game logic is separated from the interface for future GUI polish.
- No third-party Python dependencies are required.

## Run the Console Game

```bash
python3 "Triangle Peg solitaire FINAL.py"
```

You can also run the newer module entry point:

```bash
python3 -m peg_solitaire.console
```

## Run the GUI Game

The GUI is the main version to try first:

```bash
python3 -m peg_solitaire.gui
```

Or use the graphical launcher:

```bash
python3 "Triangle Peg Solitaire GUI.py"
```

## Run Tests

```bash
python3 -m unittest discover -s tests
```

## Project Layout

- `peg_solitaire/game.py` contains the board, move validation, scoring, and other
  GUI-ready rules.
- `peg_solitaire/console.py` contains the text interface, prompts, save files,
  and the polished funny messages.
- `peg_solitaire/gui.py` contains the desktop interface with a wooden board-game
  panel, blue guide lines, white pegs, and a dark tabletop backdrop.
- `Triangle Peg solitaire FINAL.py` is kept as a compatibility launcher for the
  original filename.
- `Triangle Peg Solitaire GUI.py` is a simple launcher for the graphical game.
- `assets/wood_board.png` is the wood texture used by the GUI board.
- `tests/test_game.py` covers the core board rules and scoring behavior.
- `tests/test_gui_assets.py` verifies that the GUI asset is present.

## Original Inspiration

The solution was inspired by George I. Bell's mathematical work on triangular
peg solitaire:

- https://arxiv.org/abs/math/0703865
- http://www.gibell.net/pegsolitaire/tindex.html

When I was very young, my parents bought me a wooden board game to keep me
entertained on road trips. This was before video games were portable, so one of
the games I played was the Original IQ Tester. That game is what inspired this
project.

The triangle can be expanded to larger boards, and the rules adapt to the row
count. The minimum playable board here is four rows.
