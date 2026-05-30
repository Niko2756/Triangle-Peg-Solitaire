"""Tkinter GUI for Triangle Peg Solitaire."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .game import MIN_ROWS, InvalidMove, Move, TrianglePegSolitaire, score_board


ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
WOOD_TEXTURE = ASSET_DIR / "wood_board.png"
MAX_ROWS = 10


class PegSolitaireApp:
    """Desktop game interface with a wooden board and white pegs."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Triangle Peg Solitaire")
        self.root.minsize(880, 640)

        self.rows_var = tk.IntVar(value=5)
        self.score_var = tk.StringVar(value="Score: 0")
        self.pegs_var = tk.StringVar(value="")
        self.moves_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")

        self.game = TrianglePegSolitaire(rows=self.rows_var.get())
        self.history: list[tuple[list[int], int | None, int | None, int]] = []
        self.selected_peg: int | None = None
        self.hint_move: Move | None = None
        self.session_score = 0
        self.hole_positions: dict[int, tuple[float, float, float]] = {}
        self.board_bbox: tuple[int, int, int, int] | None = None
        self.wood_texture: tk.PhotoImage | None = None
        self.board_texture: tk.PhotoImage | None = None
        self.board_texture_size: tuple[int, int] | None = None
        self.table_fill = "#20251f"

        self._load_assets()
        self._configure_style()
        self._build_layout()
        self.new_game()

    def _load_assets(self) -> None:
        if WOOD_TEXTURE.exists():
            self.wood_texture = tk.PhotoImage(file=str(WOOD_TEXTURE))

    def _configure_style(self) -> None:
        self.root.configure(bg="#161a16")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Game.TFrame",
            background="#20251f",
        )
        style.configure(
            "Side.TFrame",
            background="#24241f",
        )
        style.configure(
            "Title.TLabel",
            background="#24241f",
            foreground="#fff7e8",
            font=("Helvetica", 20, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background="#24241f",
            foreground="#e8dcc9",
            font=("Helvetica", 12),
        )
        style.configure(
            "Stat.TLabel",
            background="#24241f",
            foreground="#fff7e8",
            font=("Helvetica", 13, "bold"),
        )
        style.configure(
            "Game.TButton",
            background="#f2eee6",
            foreground="#24241f",
            font=("Helvetica", 12, "bold"),
            borderwidth=0,
            padding=(12, 8),
        )
        style.map(
            "Game.TButton",
            background=[("active", "#ffffff"), ("disabled", "#8f877c")],
            foreground=[("disabled", "#4d4238")],
        )

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            bg=self.table_fill,
            cursor="hand2",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Button-1>", self._on_board_click)
        self.canvas.bind("<Motion>", self._on_motion)

        sidebar = ttk.Frame(self.root, style="Side.TFrame", padding=22)
        sidebar.grid(row=0, column=1, sticky="ns")
        sidebar.columnconfigure(0, weight=1)

        ttk.Label(sidebar, text="Triangle Peg Solitaire", style="Title.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 14),
        )
        ttk.Label(
            sidebar,
            text="Wooden triangle board. White pegs. Tiny decisions with consequences.",
            style="Body.TLabel",
            wraplength=260,
        ).grid(row=1, column=0, sticky="w", pady=(0, 22))

        row_box = ttk.Frame(sidebar, style="Side.TFrame")
        row_box.grid(row=2, column=0, sticky="ew", pady=(0, 18))
        row_box.columnconfigure(1, weight=1)
        ttk.Label(row_box, text="Rows", style="Body.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 12),
        )
        self.row_spinbox = tk.Spinbox(
            row_box,
            from_=MIN_ROWS,
            to=MAX_ROWS,
            textvariable=self.rows_var,
            width=5,
            font=("Helvetica", 12),
            justify="center",
            bg="#fff7e8",
            fg="#2b211b",
            buttonbackground="#d9c5a3",
            relief="flat",
        )
        self.row_spinbox.grid(row=0, column=1, sticky="e")

        ttk.Button(
            sidebar,
            text="New Game",
            style="Game.TButton",
            command=self.new_game,
        ).grid(row=3, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(
            sidebar,
            text="Undo",
            style="Game.TButton",
            command=self.undo,
        ).grid(row=4, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(
            sidebar,
            text="Hint",
            style="Game.TButton",
            command=self.show_hint,
        ).grid(row=5, column=0, sticky="ew", pady=(0, 22))

        ttk.Separator(sidebar).grid(row=6, column=0, sticky="ew", pady=(0, 18))
        ttk.Label(sidebar, textvariable=self.score_var, style="Stat.TLabel").grid(
            row=7,
            column=0,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Label(sidebar, textvariable=self.pegs_var, style="Body.TLabel").grid(
            row=8,
            column=0,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Label(sidebar, textvariable=self.moves_var, style="Body.TLabel").grid(
            row=9,
            column=0,
            sticky="w",
            pady=(0, 22),
        )
        ttk.Label(
            sidebar,
            textvariable=self.status_var,
            style="Body.TLabel",
            wraplength=260,
        ).grid(row=10, column=0, sticky="new")
        sidebar.rowconfigure(10, weight=1)

    def new_game(self) -> None:
        rows = self._safe_rows()
        self.rows_var.set(rows)
        self.game = TrianglePegSolitaire(rows=rows)
        self.history.clear()
        self.selected_peg = None
        self.hint_move = None
        self.status_var.set("Pick one white peg to remove and begin.")
        self._update_stats()
        self._draw_board()

    def undo(self) -> None:
        if not self.history:
            self.status_var.set("Nothing to undo. The board is already innocent.")
            return

        pegs, starting_empty, selected_peg, session_score = self.history.pop()
        self.game = TrianglePegSolitaire.from_pegs(
            rows=self.game.rows,
            pegs=pegs,
            starting_empty=starting_empty,
        )
        self.selected_peg = selected_peg
        self.session_score = session_score
        self.hint_move = None
        self.status_var.set("Undone. The pegs are pretending this never happened.")
        self._update_stats()
        self._draw_board()

    def show_hint(self) -> None:
        moves = self.game.possible_moves()
        if not moves:
            self.status_var.set("No moves left. The board has closed its case.")
            return

        self.hint_move = moves[0]
        self.selected_peg = self.hint_move.start
        self.status_var.set(
            f"Hint: try moving peg {self.hint_move.start} to "
            f"hole {self.hint_move.end}."
        )
        self._draw_board()

    def _safe_rows(self) -> int:
        try:
            rows = int(self.rows_var.get())
        except (tk.TclError, ValueError):
            rows = 5
        return min(MAX_ROWS, max(MIN_ROWS, rows))

    def _save_history(self) -> None:
        self.history.append(
            (
                list(self.game.pegs),
                self.game.starting_empty,
                self.selected_peg,
                self.session_score,
            )
        )

    def _on_canvas_resize(self, _event: tk.Event[tk.Canvas]) -> None:
        self._draw_board()

    def _on_motion(self, event: tk.Event[tk.Canvas]) -> None:
        index = self._hole_at(event.x, event.y)
        if index is None:
            self.canvas.configure(cursor="")
        else:
            self.canvas.configure(cursor="hand2")

    def _on_board_click(self, event: tk.Event[tk.Canvas]) -> None:
        index = self._hole_at(event.x, event.y)
        if index is None:
            return

        if self.game.starting_empty is None:
            if self.game.pegs[index] == 1:
                self._save_history()
                self.game.remove_starting_peg(index)
                self.status_var.set(
                    "Good. The first peg has left the building. "
                    "Now jump a peg into an empty hole."
                )
                self._update_stats()
                self._draw_board()
            return

        if not self.game.has_moves():
            self.status_var.set("This round is finished. Start a new board.")
            return

        if self.selected_peg is None:
            self._select_peg(index)
            return

        if index == self.selected_peg:
            self.selected_peg = None
            self.hint_move = None
            self.status_var.set("Peg unselected. It will try not to take it personally.")
            self._draw_board()
            return

        if self.game.pegs[index] == 1:
            self._select_peg(index)
            return

        self._try_move(self.selected_peg, index)

    def _select_peg(self, index: int) -> None:
        if self.game.pegs[index] != 1:
            self.status_var.set("That hole is empty. Pick a white peg first.")
            return

        self.selected_peg = index
        self.hint_move = None
        self.status_var.set(f"Peg {index} selected. Choose an empty landing hole.")
        self._draw_board()

    def _try_move(self, start: int, end: int) -> None:
        try:
            self.game.validate_move(start, end)
        except InvalidMove as exc:
            self.status_var.set(f"{exc} The board is strict, but fair.")
            self._draw_board()
            return

        self._save_history()
        move = self.game.apply_move(start, end)
        self.selected_peg = None
        self.hint_move = None

        if self.game.has_moves():
            self.status_var.set(
                f"Nice jump: {move.start} over {move.over} into {move.end}."
            )
        else:
            score = score_board(self.game.pegs, self.game.starting_empty)
            self.session_score += score.points
            self.status_var.set(f"{score.title} {score.message}")

        self._update_stats()
        self._draw_board()

    def _update_stats(self) -> None:
        self.score_var.set(f"Score: {self.session_score}")
        self.pegs_var.set(f"Pegs remaining: {self.game.remaining_pegs}")

        if self.game.starting_empty is None:
            self.moves_var.set("Moves available: choose a starting peg")
        else:
            move_count = self.game.possible_move_count()
            label = "move" if move_count == 1 else "moves"
            self.moves_var.set(f"Moves available: {move_count} {label}")

    def _draw_board(self) -> None:
        if not hasattr(self, "canvas"):
            return

        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        self._draw_tabletop(width, height)
        self.hole_positions = self._calculate_hole_positions(width, height)
        self._calculate_board_geometry()
        self._draw_wooden_game_board()
        self._draw_guide_lines()
        self._draw_holes_and_pegs()

    def _draw_tabletop(self, width: int, height: int) -> None:
        self.canvas.create_rectangle(0, 0, width, height, fill=self.table_fill, width=0)
        self.canvas.create_rectangle(
            0,
            0,
            width,
            height,
            outline="#11140f",
            width=26,
        )
        self.canvas.create_line(
            0,
            height - 18,
            width,
            height - 18,
            fill="#121710",
            width=36,
        )

    def _calculate_hole_positions(
        self,
        width: int,
        height: int,
    ) -> dict[int, tuple[float, float, float]]:
        usable_width = width * 0.78
        usable_height = height * 0.76
        spacing_x = usable_width / max(1, self.game.rows)
        spacing_y = usable_height / max(1, self.game.rows)
        spacing = min(spacing_x, spacing_y)
        radius = max(14, min(34, spacing * 0.28))
        center_x = width / 2
        top_y = (height - ((self.game.rows - 1) * spacing)) / 2
        positions: dict[int, tuple[float, float, float]] = {}

        for index, (column, row) in enumerate(
            self.game.position_for_index(i) for i in range(self.game.total_holes)
        ):
            row_width = row * spacing
            x = center_x - (row_width / 2) + (column * spacing)
            y = top_y + (row * spacing)
            positions[index] = (x, y, radius)
        return positions

    def _calculate_board_geometry(self) -> None:
        if not self.hole_positions:
            self.board_bbox = None
            return

        xs = [x for x, _y, _radius in self.hole_positions.values()]
        ys = [y for _x, y, _radius in self.hole_positions.values()]
        radius = next(iter(self.hole_positions.values()))[2]
        horizontal_padding = radius * 3.15
        vertical_padding = radius * 3.05
        self.board_bbox = (
            int(min(xs) - horizontal_padding),
            int(min(ys) - vertical_padding),
            int(max(xs) + horizontal_padding),
            int(max(ys) + vertical_padding),
        )

    def _draw_wooden_game_board(self) -> None:
        if self.board_bbox is None:
            return

        left, top, right, bottom = self.board_bbox
        self.canvas.create_rectangle(
            left + 18,
            top + 22,
            right + 18,
            bottom + 22,
            fill="#090a08",
            outline="",
            stipple="gray25",
        )
        self.canvas.create_rectangle(
            left + 10,
            bottom - 2,
            right + 13,
            bottom + 18,
            fill="#4d260f",
            outline="",
        )
        self.canvas.create_rectangle(
            right - 2,
            top + 8,
            right + 13,
            bottom + 18,
            fill="#3c1d0c",
            outline="",
        )

        if self.wood_texture is None:
            self.canvas.create_rectangle(
                left,
                top,
                right,
                bottom,
                fill="#9b5725",
                outline="",
            )
        else:
            self._draw_board_wood_texture()

        self._draw_procedural_grain(stipple="gray25" if self.wood_texture else None)
        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            outline="#351807",
            width=7,
            fill="",
        )
        self.canvas.create_line(
            left + 5,
            top + 5,
            right - 7,
            top + 5,
            fill="#cf8b49",
            width=3,
        )
        self.canvas.create_line(
            left + 5,
            top + 5,
            left + 5,
            bottom - 7,
            fill="#c57b37",
            width=3,
        )
        self.canvas.create_rectangle(
            left + 5,
            top + 5,
            right - 5,
            bottom - 5,
            outline="#e2a45f",
            width=2,
            fill="",
        )

    def _draw_board_wood_texture(self) -> None:
        if self.board_bbox is None or self.wood_texture is None:
            return

        left, top, right, bottom = self.board_bbox
        width = max(1, right - left)
        height = max(1, bottom - top)
        if self.board_texture_size != (width, height):
            self.board_texture = tk.PhotoImage(width=width, height=height)
            texture_width = self.wood_texture.width()
            texture_height = self.wood_texture.height()
            for x in range(0, width, texture_width):
                for y in range(0, height, texture_height):
                    copy_width = min(texture_width, width - x)
                    copy_height = min(texture_height, height - y)
                    self.board_texture.tk.call(
                        self.board_texture,
                        "copy",
                        self.wood_texture,
                        "-from",
                        0,
                        0,
                        copy_width,
                        copy_height,
                        "-to",
                        x,
                        y,
                    )
            self.board_texture_size = (width, height)

        self.canvas.create_image(left, top, anchor="nw", image=self.board_texture)

    def _draw_procedural_grain(self, stipple: str | None = None) -> None:
        if self.board_bbox is None:
            return

        left, top, right, bottom = self.board_bbox
        height = max(1, bottom - top)
        for line_number in range(42):
            y = top + ((line_number + 1) * height / 44)
            wave = ((line_number % 5) - 2) * 0.65
            color = ("#5c2a10", "#784018", "#c37a39", "#e3a85b")[line_number % 4]
            width = 1 if line_number % 3 else 2
            line_options = {"fill": color, "width": width}
            if stipple is not None:
                line_options["stipple"] = stipple
            self.canvas.create_line(
                left + 12,
                y + wave,
                right - 12,
                y - wave,
                **line_options,
            )

    def _draw_guide_lines(self) -> None:
        for start, end in self._guide_line_pairs():
            x1, y1, radius = self.hole_positions[start]
            x2, y2, _radius = self.hole_positions[end]
            dx = x2 - x1
            dy = y2 - y1
            distance = max(1.0, ((dx * dx) + (dy * dy)) ** 0.5)
            gap = radius * 1.45
            start_x = x1 + (dx / distance) * gap
            start_y = y1 + (dy / distance) * gap
            end_x = x2 - (dx / distance) * gap
            end_y = y2 - (dy / distance) * gap
            self.canvas.create_line(
                start_x,
                start_y,
                end_x,
                end_y,
                fill="#1d65c9",
                width=max(4, int(radius * 0.20)),
                capstyle=tk.ROUND,
            )
            self.canvas.create_line(
                start_x,
                start_y,
                end_x,
                end_y,
                fill="#4692ff",
                width=max(2, int(radius * 0.11)),
                capstyle=tk.ROUND,
            )

    def _guide_line_pairs(self) -> list[tuple[int, int]]:
        pairs: list[tuple[int, int]] = []
        directions = ((0, 1), (1, 1), (1, 0))
        for start in range(self.game.total_holes):
            column, row = self.game.position_for_index(start)
            for column_delta, row_delta in directions:
                end = self.game.index_for_position(
                    column + column_delta,
                    row + row_delta,
                )
                if end is not None:
                    pairs.append((start, end))
        return pairs

    def _draw_holes_and_pegs(self) -> None:
        valid_destinations = self._selected_destinations()
        hint_positions = set()
        if self.hint_move is not None:
            hint_positions = {
                self.hint_move.start,
                self.hint_move.over,
                self.hint_move.end,
            }

        for index, (x, y, radius) in self.hole_positions.items():
            selected = index == self.selected_peg
            hinted = index in hint_positions
            destination = index in valid_destinations

            self._draw_hole(x, y, radius, destination=destination, hinted=hinted)
            if self.game.pegs[index] == 1:
                self._draw_white_peg(x, y, radius, selected=selected, hinted=hinted)

    def _selected_destinations(self) -> set[int]:
        if self.selected_peg is None:
            return set()
        return {
            move.end
            for move in self.game.possible_moves()
            if move.start == self.selected_peg
        }

    def _draw_hole(
        self,
        x: float,
        y: float,
        radius: float,
        *,
        destination: bool,
        hinted: bool,
    ) -> None:
        self.canvas.create_oval(
            x - radius * 1.08,
            y - radius * 0.92,
            x + radius * 1.08,
            y + radius * 1.18,
            fill="#261409",
            outline="#9b5a2c",
            width=2,
        )
        self.canvas.create_oval(
            x - radius * 0.78,
            y - radius * 0.68,
            x + radius * 0.78,
            y + radius * 0.82,
            fill="#120b07",
            outline="#100906",
            width=1,
        )

        if destination or hinted:
            self.canvas.create_oval(
                x - radius * 1.34,
                y - radius * 1.20,
                x + radius * 1.34,
                y + radius * 1.46,
                outline="#fff3c2",
                width=3,
            )

    def _draw_white_peg(
        self,
        x: float,
        y: float,
        radius: float,
        *,
        selected: bool,
        hinted: bool,
    ) -> None:
        peg_radius = radius * 0.92
        self.canvas.create_oval(
            x - peg_radius * 0.92,
            y - peg_radius * 0.42,
            x + peg_radius * 1.04,
            y + peg_radius * 1.18,
            fill="#1d120a",
            outline="",
            stipple="gray50",
        )

        rings = [
            (1.00, "#d8d1c3"),
            (0.84, "#eee8dc"),
            (0.66, "#fffaf0"),
            (0.44, "#ffffff"),
        ]
        for scale, color in rings:
            self.canvas.create_oval(
                x - peg_radius * scale,
                y - peg_radius * scale,
                x + peg_radius * scale,
                y + peg_radius * scale,
                fill=color,
                outline="#c3b8a9" if scale == 1.00 else color,
                width=2 if scale == 1.00 else 1,
            )

        self.canvas.create_oval(
            x - peg_radius * 0.48,
            y - peg_radius * 0.58,
            x - peg_radius * 0.04,
            y - peg_radius * 0.18,
            fill="#ffffff",
            outline="",
        )
        self.canvas.create_arc(
            x - peg_radius * 0.86,
            y - peg_radius * 0.78,
            x + peg_radius * 0.86,
            y + peg_radius * 0.86,
            start=210,
            extent=115,
            style="arc",
            outline="#b8ac9a",
            width=3,
        )

        if selected or hinted:
            self.canvas.create_oval(
                x - peg_radius * 1.22,
                y - peg_radius * 1.22,
                x + peg_radius * 1.22,
                y + peg_radius * 1.22,
                outline="#fff3c2",
                width=4,
            )

    def _hole_at(self, x: float, y: float) -> int | None:
        for index, (hole_x, hole_y, radius) in self.hole_positions.items():
            dx = x - hole_x
            dy = y - hole_y
            if (dx * dx) + (dy * dy) <= (radius * 1.25) ** 2:
                return index
        return None


def main() -> None:
    root = tk.Tk()
    PegSolitaireApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
