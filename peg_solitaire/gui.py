"""Tkinter GUI for Triangle Peg Solitaire."""

from __future__ import annotations

import math
import shutil
import struct
import subprocess
import sys
import tempfile
import tkinter as tk
import wave
import ctypes
import ctypes.util
from pathlib import Path
from tkinter import ttk

from .game import (
    MIN_ROWS,
    InvalidMove,
    Move,
    ScoreResult,
    TrianglePegSolitaire,
    score_board,
)
from .storage import (
    ANIMATION_SPEEDS,
    CURSOR_MODES,
    DEFAULT_STATS_PATH,
    GameStats,
    StatsUpdate,
    load_stats,
    record_game,
    save_stats,
)


ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
WOOD_TEXTURE = ASSET_DIR / "wood_board.png"
GAME_CURSOR = ASSET_DIR / "game_cursor.png"
MAX_ROWS = 10


class SoundEffects:
    """Small generated sound effects with no third-party dependencies."""

    SAMPLE_RATE = 44_100

    def __init__(self) -> None:
        self.enabled = True
        self.player = self._find_player()
        self.sound_dir = Path(tempfile.gettempdir()) / "triangle_peg_solitaire_sounds"
        self.files = {
            "pickup": self.sound_dir / "pickup.wav",
            "lift": self.sound_dir / "lift.wav",
            "slot": self.sound_dir / "slot.wav",
            "invalid": self.sound_dir / "invalid.wav",
            "game_over": self.sound_dir / "game_over.wav",
        }
        self._prepare_files()

    def play(self, name: str) -> None:
        if not self.enabled:
            return

        path = self.files.get(name)
        if path is None or not path.exists():
            return

        if sys.platform.startswith("win"):
            try:
                import winsound

                winsound.PlaySound(
                    str(path),
                    winsound.SND_FILENAME | winsound.SND_ASYNC,
                )
            except RuntimeError:
                pass
            return

        if self.player is None:
            return

        try:
            subprocess.Popen(
                [self.player, str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            self.enabled = False

    def _find_player(self) -> str | None:
        if sys.platform.startswith("darwin"):
            return shutil.which("afplay")
        for candidate in ("paplay", "aplay", "pw-play"):
            player = shutil.which(candidate)
            if player:
                return player
        return None

    def _prepare_files(self) -> None:
        try:
            self.sound_dir.mkdir(parents=True, exist_ok=True)
            self._write_tone(
                self.files["pickup"],
                [(620, 0.035, 0.20), (840, 0.045, 0.16)],
            )
            self._write_tone(
                self.files["lift"],
                [(420, 0.035, 0.12), (620, 0.045, 0.16), (920, 0.070, 0.14)],
            )
            self._write_tone(
                self.files["slot"],
                [(165, 0.040, 0.34), (92, 0.055, 0.24), (260, 0.030, 0.10)],
            )
            self._write_tone(
                self.files["invalid"],
                [(160, 0.070, 0.20), (118, 0.070, 0.18)],
            )
            self._write_tone(
                self.files["game_over"],
                [(392, 0.070, 0.16), (523, 0.075, 0.17), (659, 0.110, 0.16)],
            )
        except OSError:
            self.enabled = False

    def _write_tone(
        self,
        path: Path,
        notes: list[tuple[float, float, float]],
    ) -> None:
        samples: list[int] = []
        for frequency, duration, volume in notes:
            sample_count = int(self.SAMPLE_RATE * duration)
            for index in range(sample_count):
                progress = index / max(1, sample_count - 1)
                envelope = math.sin(math.pi * progress)
                overtone = 0.35 * math.sin(
                    2.0 * math.pi * frequency * 2.0 * index / self.SAMPLE_RATE
                )
                value = math.sin(
                    2.0 * math.pi * frequency * index / self.SAMPLE_RATE
                )
                samples.append(int(32767 * volume * envelope * (value + overtone)))

        with wave.open(str(path), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(
                b"".join(struct.pack("<h", sample) for sample in samples)
            )


class FriendlyButton(tk.Canvas):
    """Canvas-drawn button so colors stay readable on macOS and Windows."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        text: str,
        command,
        width: int = 280,
        height: int = 48,
        bg: str = "#111410",
        fill: str = "#fff4df",
        hover_fill: str = "#ffffff",
        active_fill: str = "#f4d18f",
        text_color: str = "#1a130c",
        outline: str = "#d9a85d",
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor="arrow",
        )
        self.label = text
        self.command = command
        self.fill = fill
        self.hover_fill = hover_fill
        self.active_fill = active_fill
        self.text_color = text_color
        self.outline = outline
        self.is_hovered = False
        self.is_pressed = False
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self._draw()

    def _on_enter(self, _event: tk.Event[tk.Canvas]) -> None:
        self.is_hovered = True
        self._draw()

    def _on_leave(self, _event: tk.Event[tk.Canvas]) -> None:
        self.is_hovered = False
        self.is_pressed = False
        self._draw()

    def _on_press(self, _event: tk.Event[tk.Canvas]) -> None:
        self.is_pressed = True
        self._draw()

    def _on_release(self, event: tk.Event[tk.Canvas]) -> None:
        should_run = (
            self.is_pressed
            and 0 <= event.x <= self.winfo_width()
            and 0 <= event.y <= self.winfo_height()
        )
        self.is_pressed = False
        self._draw()
        if should_run:
            self.command()

    def _draw(self) -> None:
        self.delete("all")
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        fill = self.active_fill if self.is_pressed else self.fill
        if self.is_hovered and not self.is_pressed:
            fill = self.hover_fill

        y_offset = 2 if self.is_pressed else 0
        self._rounded_rect(
            3,
            5 + y_offset,
            width - 3,
            height - 5 + y_offset,
            radius=14,
            fill="#0b0d0a",
            outline="",
        )
        self._rounded_rect(
            2,
            2 + y_offset,
            width - 2,
            height - 8 + y_offset,
            radius=14,
            fill=fill,
            outline=self.outline,
            width=2,
        )
        self.create_text(
            width / 2,
            (height / 2) - 2 + y_offset,
            text=self.label,
            fill=self.text_color,
            font=("Helvetica", 13, "bold"),
        )

    def _rounded_rect(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        radius: float,
        fill: str,
        outline: str,
        width: int = 1,
    ) -> None:
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        self.create_polygon(
            points,
            smooth=True,
            splinesteps=12,
            fill=fill,
            outline=outline,
            width=width,
        )


class RowSelector(tk.Canvas):
    """Canvas row picker that avoids the tiny native spinbox."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        value: int,
        command,
        minimum: int = MIN_ROWS,
        maximum: int = MAX_ROWS,
        bg: str = "#111410",
    ) -> None:
        super().__init__(
            parent,
            width=260,
            height=62,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor="arrow",
        )
        self.value = value
        self.command = command
        self.minimum = minimum
        self.maximum = maximum
        self.hover_zone: str | None = None
        self.press_zone: str | None = None
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self._draw()

    def set_value(self, value: int) -> None:
        self.value = min(self.maximum, max(self.minimum, value))
        self._draw()

    def _on_motion(self, event: tk.Event[tk.Canvas]) -> None:
        zone = self._zone_at(event.x, event.y)
        if zone != self.hover_zone:
            self.hover_zone = zone
            self._draw()

    def _on_leave(self, _event: tk.Event[tk.Canvas]) -> None:
        self.hover_zone = None
        self.press_zone = None
        self._draw()

    def _on_press(self, event: tk.Event[tk.Canvas]) -> None:
        self.press_zone = self._zone_at(event.x, event.y)
        self._draw()

    def _on_release(self, event: tk.Event[tk.Canvas]) -> None:
        zone = self._zone_at(event.x, event.y)
        should_adjust = self.press_zone == zone and zone in ("minus", "plus")
        self.press_zone = None
        if should_adjust:
            delta = -1 if zone == "minus" else 1
            new_value = min(self.maximum, max(self.minimum, self.value + delta))
            if new_value != self.value:
                self.value = new_value
                self.command(new_value)
        self._draw()

    def _zone_at(self, x: float, y: float) -> str | None:
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        if not 0 <= y <= height:
            return None
        if 6 <= x <= 62:
            return "minus"
        if width - 62 <= x <= width - 6:
            return "plus"
        if 62 < x < width - 62:
            return "value"
        return None

    def _draw(self) -> None:
        self.delete("all")
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        self._rounded_rect(4, 7, width - 4, height - 5, 16, "#080a08", "")
        self._rounded_rect(2, 2, width - 2, height - 9, 16, "#fff4df", "#d9a85d", 2)
        self.create_text(
            width / 2,
            (height / 2) - 4,
            text=str(self.value),
            fill="#1d130a",
            font=("Helvetica", 20, "bold"),
        )

        self._draw_adjust_button(8, 8, 58, height - 15, "minus", "-")
        self._draw_adjust_button(width - 58, 8, width - 8, height - 15, "plus", "+")

    def _draw_adjust_button(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        zone: str,
        label: str,
    ) -> None:
        fill = "#f1d49f"
        if self.hover_zone == zone:
            fill = "#ffe9bd"
        if self.press_zone == zone:
            fill = "#dba65e"
        self._rounded_rect(x1, y1, x2, y2, 12, fill, "#b77a32", 2)
        self.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2 - 2,
            text=label,
            fill="#1d130a",
            font=("Helvetica", 20, "bold"),
        )

    def _rounded_rect(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: float,
        fill: str,
        outline: str,
        width: int = 1,
    ) -> None:
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        self.create_polygon(
            points,
            smooth=True,
            splinesteps=12,
            fill=fill,
            outline=outline,
            width=width,
        )


class NativeMacCursor:
    """Best-effort Cocoa cursor that uses the PNG asset without hiding the arrow."""

    def __init__(self, image_path: Path, size: float = 30.0) -> None:
        self.available = False
        self.active = False
        self.cursor: int | None = None
        self.arrow_cursor: int | None = None
        self.objc = None
        self.msg = None

        if not sys.platform.startswith("darwin") or not image_path.exists():
            return

        try:
            objc_path = ctypes.util.find_library("objc")
            appkit_path = ctypes.util.find_library("AppKit")
            if objc_path is None or appkit_path is None:
                return

            self.objc = ctypes.cdll.LoadLibrary(objc_path)
            ctypes.cdll.LoadLibrary(appkit_path)
            self.msg = self.objc.objc_msgSend
            self.objc.objc_getClass.restype = ctypes.c_void_p
            self.objc.objc_getClass.argtypes = [ctypes.c_char_p]
            self.objc.sel_registerName.restype = ctypes.c_void_p
            self.objc.sel_registerName.argtypes = [ctypes.c_char_p]

            self._call0("NSApplication", "sharedApplication")
            image_path_string = self._call1_string(
                "NSString",
                "stringWithUTF8String:",
                str(image_path).encode(),
            )
            image = self._send1_id(
                self._call0("NSImage", "alloc"),
                "initWithContentsOfFile:",
                image_path_string,
            )
            if not image:
                return

            self._set_image_size(image, size)
            self.cursor = self._create_cursor(image)
            self.arrow_cursor = self._call0("NSCursor", "arrowCursor")
            self.available = self.cursor is not None and self.arrow_cursor is not None
        except (AttributeError, OSError, TypeError, ValueError, ctypes.ArgumentError):
            self.available = False
            self.cursor = None
            self.arrow_cursor = None

    def set_custom(self) -> None:
        if not self.available or self.cursor is None:
            return
        try:
            self._send_void(self.cursor, "set")
            self.active = True
        except (AttributeError, OSError, TypeError, ValueError, ctypes.ArgumentError):
            self.available = False

    def set_arrow(self) -> None:
        if not self.available or self.arrow_cursor is None:
            return
        try:
            self._send_void(self.arrow_cursor, "set")
            self.active = False
        except (AttributeError, OSError, TypeError, ValueError, ctypes.ArgumentError):
            self.available = False

    def _class(self, name: str) -> int:
        return self.objc.objc_getClass(name.encode())

    def _selector(self, name: str) -> int:
        return self.objc.sel_registerName(name.encode())

    def _call0(self, class_name: str, selector: str) -> int:
        return self._send0(self._class(class_name), selector)

    def _call1_string(self, class_name: str, selector: str, value: bytes) -> int:
        self.msg.restype = ctypes.c_void_p
        self.msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p]
        return self.msg(self._class(class_name), self._selector(selector), value)

    def _send0(self, receiver: int, selector: str) -> int:
        self.msg.restype = ctypes.c_void_p
        self.msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        return self.msg(receiver, self._selector(selector))

    def _send1_id(self, receiver: int, selector: str, value: int) -> int:
        self.msg.restype = ctypes.c_void_p
        self.msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        return self.msg(receiver, self._selector(selector), value)

    def _send_void(self, receiver: int, selector: str) -> None:
        self.msg.restype = None
        self.msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self.msg(receiver, self._selector(selector))

    def _set_image_size(self, image: int, size: float) -> None:
        class NSSize(ctypes.Structure):
            _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]

        self.msg.restype = None
        self.msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, NSSize]
        self.msg(image, self._selector("setSize:"), NSSize(size, size))

    def _create_cursor(self, image: int) -> int:
        class NSPoint(ctypes.Structure):
            _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

        cursor_alloc = self._call0("NSCursor", "alloc")
        self.msg.restype = ctypes.c_void_p
        self.msg.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            NSPoint,
        ]
        return self.msg(
            cursor_alloc,
            self._selector("initWithImage:hotSpot:"),
            image,
            NSPoint(1.0, 1.0),
        )


class CursorManager:
    """Applies one visible cursor policy across every game window."""

    POLL_MS = 25
    TITLEBAR_GUARD_PX = 48

    def __init__(self, root: tk.Tk, image_path: Path) -> None:
        self.root = root
        self.native_cursor = NativeMacCursor(image_path)
        self.cursor_value = "arrow"
        self.mode = "auto"
        self.windows: set[tk.Toplevel | tk.Tk] = {root}
        self.configured_widgets: set[str] = set()
        self.poll_after_id: str | None = None
        self.refresh_after_id: str | None = None
        self.root.bind("<Destroy>", self._on_destroy, add="+")

    def attach(self, widget: tk.Widget) -> None:
        self.apply_cursor(widget)

    def register_window(self, window: tk.Toplevel | tk.Tk) -> None:
        self.windows.add(window)
        self.apply_cursor(window)
        window.bind("<Enter>", self._activate, add="+")
        window.bind("<Motion>", self._activate, add="+")
        window.bind("<Leave>", lambda _event: self._reset_if_outside(), add="+")
        window.bind("<Destroy>", self._on_destroy, add="+")
        self.start()

    def unregister_window(self, window: tk.Toplevel | tk.Tk) -> None:
        self.windows.discard(window)
        self._reset_if_outside()

    def apply_cursor(self, widget: tk.Widget) -> None:
        widget_id = str(widget)
        if widget_id in self.configured_widgets:
            return

        self.configured_widgets.add(widget_id)
        try:
            widget.configure(cursor=self.cursor_value)
        except (tk.TclError, TypeError):
            pass

        widget.bind("<Enter>", self._activate, add="+")
        widget.bind("<Motion>", self._activate, add="+")
        widget.bind("<Leave>", lambda _event: self._reset_if_outside(), add="+")
        widget.bind("<Map>", lambda event: self.apply_cursor(event.widget), add="+")
        for child in widget.winfo_children():
            self.apply_cursor(child)

    def redraw(self, _canvas: tk.Canvas) -> None:
        self._activate()

    def set_mode(self, mode: str) -> None:
        self.mode = mode if mode in CURSOR_MODES else "auto"
        if self.mode == "system":
            self.native_cursor.set_arrow()
        else:
            self._activate()

    def start(self) -> None:
        if self.poll_after_id is None:
            self._poll_pointer()

    def stop(self) -> None:
        if self.poll_after_id is not None:
            try:
                self.root.after_cancel(self.poll_after_id)
            except tk.TclError:
                pass
            self.poll_after_id = None
        if self.refresh_after_id is not None:
            try:
                self.root.after_cancel(self.refresh_after_id)
            except tk.TclError:
                pass
            self.refresh_after_id = None
        self.native_cursor.set_arrow()

    def _activate(self, _event: tk.Event[tk.Widget] | None = None) -> None:
        if self.refresh_after_id is not None:
            return
        try:
            self.refresh_after_id = self.root.after_idle(self._apply_current_pointer)
        except tk.TclError:
            self.refresh_after_id = None

    def _reset_if_outside(self) -> None:
        self._apply_current_pointer()

    def _poll_pointer(self) -> None:
        self._apply_current_pointer()
        try:
            self.poll_after_id = self.root.after(self.POLL_MS, self._poll_pointer)
        except tk.TclError:
            self.poll_after_id = None

    def _apply_current_pointer(self) -> None:
        self.refresh_after_id = None
        if self.mode == "system":
            self.native_cursor.set_arrow()
            return
        try:
            x = self.root.winfo_pointerx()
            y = self.root.winfo_pointery()
        except tk.TclError:
            return

        if self._pointer_inside_app_content(x, y):
            self.native_cursor.set_custom()
        else:
            self.native_cursor.set_arrow()

    def _pointer_inside_app_content(self, x: int, y: int) -> bool:
        try:
            widget = self.root.winfo_containing(x, y)
        except tk.TclError:
            return False

        if widget is None:
            return False
        if not self._widget_belongs_to_registered_window(widget):
            return False

        return not self._inside_titlebar_guard(widget.winfo_toplevel(), x, y)

    def _widget_belongs_to_registered_window(self, widget: tk.Widget) -> bool:
        current: tk.Widget | None = widget
        while current is not None:
            if current in self.windows:
                return True
            try:
                parent_name = current.winfo_parent()
                if not parent_name:
                    return False
                current = current.nametowidget(parent_name)
            except (KeyError, tk.TclError):
                return False
        return False

    def _inside_titlebar_guard(self, window: tk.Toplevel | tk.Tk, x: int, y: int) -> bool:
        try:
            if not window.winfo_exists() or not window.winfo_viewable():
                return False
            top = window.winfo_rooty()
            left = window.winfo_rootx()
            right = left + window.winfo_width()
        except tk.TclError:
            return False
        return left <= x < right and top <= y < top + self.TITLEBAR_GUARD_PX

    def _pointer_inside_app(self, x: int, y: int) -> bool:
        for window in list(self.windows):
            try:
                if not window.winfo_exists():
                    self.windows.discard(window)
                    continue
                if not window.winfo_viewable():
                    continue
                left = window.winfo_rootx()
                top = window.winfo_rooty()
                right = left + window.winfo_width()
                bottom = top + window.winfo_height()
            except tk.TclError:
                self.windows.discard(window)
                continue
            if left <= x < right and top <= y < bottom:
                return True
        return False

    def _on_destroy(self, event: tk.Event[tk.Widget]) -> None:
        if event.widget == self.root:
            self.stop()
            return
        if event.widget in self.windows:
            self.windows.discard(event.widget)


class PegSolitaireApp:
    """Desktop game interface with a wooden board and white pegs."""

    def __init__(self, root: tk.Tk, stats_path: Path = DEFAULT_STATS_PATH) -> None:
        self.root = root
        self.root.title("Triangle Peg Solitaire")
        self.root.geometry("1280x860")
        self.root.minsize(1060, 680)
        self.stats_path = stats_path

        self.rows_var = tk.IntVar(value=5)
        self.score_var = tk.StringVar(value="Score: 0")
        self.pegs_var = tk.StringVar(value="")
        self.moves_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")
        self.player_stats_var = tk.StringVar(value="")

        self.sound = SoundEffects()
        self.stats: GameStats = load_stats(self.stats_path)
        self.sound.enabled = self.stats.sound_enabled
        self.game = TrianglePegSolitaire(rows=self.rows_var.get())
        self.history: list[tuple[list[int], int | None, int | None, int]] = []
        self.selected_peg: int | None = None
        self.hovered_hole: int | None = None
        self.hint_move: Move | None = None
        self.is_animating = False
        self.animation_move: Move | None = None
        self.animation_position: tuple[float, float, float] | None = None
        self.removed_peg_animation_position: tuple[float, float, float] | None = None
        self.removed_peg_lift_progress = 0.0
        self.animation_hidden_indexes: set[int] = set()
        self.animation_after_id: str | None = None
        self.session_score = 0
        self.hole_positions: dict[int, tuple[float, float, float]] = {}
        self.board_bbox: tuple[int, int, int, int] | None = None
        self.wood_texture: tk.PhotoImage | None = None
        self.board_texture: tk.PhotoImage | None = None
        self.board_texture_size: tuple[int, int] | None = None
        self.game_over_window: tk.Toplevel | None = None
        self.tutorial_window: tk.Toplevel | None = None
        self.settings_window: tk.Toplevel | None = None
        self.sidebar_canvas: tk.Canvas | None = None
        self.sidebar_canvas_window: int | None = None
        self.sidebar_scrollbar: ttk.Scrollbar | None = None
        self.last_stats_update: StatsUpdate | None = None
        self.cursor_sprite: tk.PhotoImage | None = None
        self.table_fill = "#191d18"

        self._load_assets()
        self.cursor_manager = CursorManager(self.root, GAME_CURSOR)
        self.cursor_manager.set_mode(self.stats.cursor_mode)
        self._configure_style()
        self._build_layout()
        self.new_game()
        self.root.after(350, self._maybe_show_tutorial)

    def _load_assets(self) -> None:
        if WOOD_TEXTURE.exists():
            try:
                self.wood_texture = tk.PhotoImage(file=str(WOOD_TEXTURE))
            except tk.TclError:
                self.wood_texture = None
        if GAME_CURSOR.exists():
            try:
                self.cursor_sprite = tk.PhotoImage(file=str(GAME_CURSOR))
            except tk.TclError:
                self.cursor_sprite = None

    def _configure_style(self) -> None:
        self.root.configure(bg="#111410")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Game.TFrame",
            background="#191d18",
        )
        style.configure(
            "Side.TFrame",
            background="#111410",
        )
        style.configure(
            "Title.TLabel",
            background="#111410",
            foreground="#fffaf0",
            font=("Helvetica", 22, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background="#111410",
            foreground="#fff2d8",
            font=("Helvetica", 13),
        )
        style.configure(
            "Stat.TLabel",
            background="#111410",
            foreground="#ffffff",
            font=("Helvetica", 15, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background="#111410",
            foreground="#d8c59f",
            font=("Helvetica", 12),
        )
        style.configure(
            "Game.TButton",
            background="#fff4df",
            foreground="#111410",
            font=("Helvetica", 12, "bold"),
            borderwidth=0,
            padding=(12, 8),
        )
        style.map(
            "Game.TButton",
            background=[("active", "#ffffff"), ("disabled", "#8f877c")],
            foreground=[("disabled", "#4d4238")],
        )
        style.configure("Readable.TSeparator", background="#6e5740")
        style.configure(
            "Sidebar.Vertical.TScrollbar",
            background="#6e5740",
            troughcolor="#111410",
            bordercolor="#111410",
            arrowcolor="#fff8ea",
            relief="flat",
            width=12,
        )

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0, minsize=430)
        self.root.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            bg=self.table_fill,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Button-1>", self._on_board_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Enter>", self._on_canvas_enter)
        self.canvas.bind("<Leave>", self._on_canvas_leave)
        self.cursor_manager.attach(self.canvas)

        sidebar_outer = tk.Frame(self.root, bg="#111410", width=430, bd=0)
        sidebar_outer.grid(row=0, column=1, sticky="ns")
        sidebar_outer.grid_propagate(False)
        sidebar_outer.columnconfigure(0, weight=1)
        sidebar_outer.rowconfigure(0, weight=1)

        self.sidebar_canvas = tk.Canvas(
            sidebar_outer,
            bg="#111410",
            highlightthickness=0,
            bd=0,
            width=416,
        )
        self.sidebar_canvas.grid(row=0, column=0, sticky="nsew")
        self.sidebar_scrollbar = ttk.Scrollbar(
            sidebar_outer,
            orient="vertical",
            command=self.sidebar_canvas.yview,
            style="Sidebar.Vertical.TScrollbar",
        )
        self.sidebar_scrollbar.grid(row=0, column=1, sticky="ns")
        self.sidebar_canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)

        sidebar = ttk.Frame(self.sidebar_canvas, style="Side.TFrame", padding=32)
        self.sidebar_canvas_window = self.sidebar_canvas.create_window(
            0,
            0,
            anchor="nw",
            window=sidebar,
        )
        sidebar.bind("<Configure>", self._on_sidebar_configure)
        self.sidebar_canvas.bind("<Configure>", self._on_sidebar_canvas_configure)
        sidebar_outer.bind("<Enter>", self._bind_sidebar_scroll, add="+")
        sidebar_outer.bind("<Leave>", self._unbind_sidebar_scroll, add="+")
        sidebar.columnconfigure(0, weight=1)

        ttk.Label(sidebar, text="Triangle Peg Solitaire", style="Title.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 12),
        )
        ttk.Label(
            sidebar,
            text="Wooden triangle board. White pegs. Tiny decisions with consequences.",
            style="Body.TLabel",
            wraplength=340,
        ).grid(row=1, column=0, sticky="w", pady=(0, 26))

        row_box = ttk.Frame(sidebar, style="Side.TFrame")
        row_box.grid(row=2, column=0, sticky="ew", pady=(0, 18))
        row_box.columnconfigure(0, weight=1)
        ttk.Label(row_box, text="Rows", style="Body.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        self.row_selector = RowSelector(
            row_box,
            bg="#111410",
            value=self.rows_var.get(),
            command=self._on_rows_changed,
        )
        self.row_selector.grid(row=1, column=0, pady=(10, 0))
        self.cursor_manager.attach(self.row_selector)

        self._make_button(
            sidebar,
            text="New Game",
            bg="#111410",
            command=self.new_game,
        ).grid(row=3, column=0, sticky="ew", pady=(0, 12))
        self._make_button(
            sidebar,
            text="Undo",
            bg="#111410",
            command=self.undo,
        ).grid(row=4, column=0, sticky="ew", pady=(0, 12))
        self._make_button(
            sidebar,
            text="Hint",
            bg="#111410",
            command=self.show_hint,
        ).grid(row=5, column=0, sticky="ew", pady=(0, 12))

        action_row = ttk.Frame(sidebar, style="Side.TFrame")
        action_row.grid(row=6, column=0, sticky="ew", pady=(0, 18))
        action_row.columnconfigure(0, weight=1)
        action_row.columnconfigure(1, weight=1)
        self._make_button(
            action_row,
            text="How to Play",
            bg="#111410",
            command=lambda: self._show_tutorial(force=True),
            width=160,
            height=44,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._make_button(
            action_row,
            text="Settings",
            bg="#111410",
            command=self._show_settings,
            width=160,
            height=44,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ttk.Separator(sidebar, style="Readable.TSeparator").grid(
            row=7,
            column=0,
            sticky="ew",
            pady=(0, 16),
        )
        ttk.Label(sidebar, textvariable=self.score_var, style="Stat.TLabel").grid(
            row=8,
            column=0,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Label(sidebar, textvariable=self.pegs_var, style="Stat.TLabel").grid(
            row=9,
            column=0,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Label(sidebar, textvariable=self.moves_var, style="Stat.TLabel").grid(
            row=10,
            column=0,
            sticky="w",
            pady=(0, 14),
        )

        player_box = tk.Frame(
            sidebar,
            bg="#171c16",
            highlightbackground="#6e5740",
            highlightcolor="#6e5740",
            highlightthickness=1,
            bd=0,
        )
        player_box.grid(row=11, column=0, sticky="ew", pady=(0, 16))
        player_box.columnconfigure(0, weight=1)
        tk.Label(
            player_box,
            text="Player Stats",
            bg="#171c16",
            fg="#fff8ea",
            font=("Helvetica", 12, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))
        tk.Message(
            player_box,
            textvariable=self.player_stats_var,
            bg="#171c16",
            fg="#f6e7c6",
            font=("Helvetica", 12),
            width=322,
            anchor="nw",
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        self.cursor_manager.apply_cursor(player_box)

        status_box = tk.Frame(
            sidebar,
            bg="#fff3dc",
            highlightbackground="#d6a45c",
            highlightcolor="#d6a45c",
            highlightthickness=2,
            bd=0,
        )
        status_box.grid(row=12, column=0, sticky="new")
        status_box.columnconfigure(0, weight=1)
        tk.Label(
            status_box,
            text="Board Status",
            bg="#fff3dc",
            fg="#24150b",
            font=("Helvetica", 12, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))
        tk.Message(
            status_box,
            textvariable=self.status_var,
            bg="#fff3dc",
            fg="#24150b",
            font=("Helvetica", 13),
            width=322,
            anchor="nw",
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        self.cursor_manager.apply_cursor(status_box)
        sidebar.rowconfigure(12, weight=1)
        self.cursor_manager.apply_cursor(sidebar_outer)
        self.cursor_manager.register_window(self.root)

    def _on_sidebar_configure(self, _event: tk.Event[ttk.Frame]) -> None:
        if self.sidebar_canvas is None:
            return
        self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))
        self._sync_sidebar_scrollbar()

    def _on_sidebar_canvas_configure(self, event: tk.Event[tk.Canvas]) -> None:
        if self.sidebar_canvas is None or self.sidebar_canvas_window is None:
            return
        self.sidebar_canvas.itemconfigure(self.sidebar_canvas_window, width=event.width)
        self._sync_sidebar_scrollbar()

    def _sync_sidebar_scrollbar(self) -> None:
        if self.sidebar_canvas is None or self.sidebar_scrollbar is None:
            return

        scrollregion = self.sidebar_canvas.cget("scrollregion")
        if not scrollregion:
            return
        try:
            _left, top, _right, bottom = map(float, scrollregion.split())
        except ValueError:
            return

        content_height = bottom - top
        canvas_height = self.sidebar_canvas.winfo_height()
        needs_scrollbar = content_height > canvas_height + 1
        if needs_scrollbar:
            if not self.sidebar_scrollbar.winfo_ismapped():
                self.sidebar_scrollbar.grid(row=0, column=1, sticky="ns")
        else:
            if self.sidebar_scrollbar.winfo_ismapped():
                self.sidebar_scrollbar.grid_remove()
            self.sidebar_canvas.yview_moveto(0.0)

    def _bind_sidebar_scroll(self, _event: tk.Event[tk.Widget]) -> None:
        if self.sidebar_canvas is None:
            return
        self.sidebar_canvas.bind_all("<MouseWheel>", self._on_sidebar_mousewheel)
        self.sidebar_canvas.bind_all("<Button-4>", self._on_sidebar_mousewheel)
        self.sidebar_canvas.bind_all("<Button-5>", self._on_sidebar_mousewheel)

    def _unbind_sidebar_scroll(self, _event: tk.Event[tk.Widget]) -> None:
        if self.sidebar_canvas is None:
            return
        self.sidebar_canvas.unbind_all("<MouseWheel>")
        self.sidebar_canvas.unbind_all("<Button-4>")
        self.sidebar_canvas.unbind_all("<Button-5>")

    def _on_sidebar_mousewheel(self, event: tk.Event[tk.Widget]) -> str:
        if self.sidebar_canvas is None:
            return "break"
        if getattr(event, "num", None) == 4:
            units = -3
        elif getattr(event, "num", None) == 5:
            units = 3
        else:
            delta = getattr(event, "delta", 0)
            units = -3 if delta > 0 else 3
        self.sidebar_canvas.yview_scroll(units, "units")
        return "break"

    def _make_button(self, parent: tk.Misc, **kwargs) -> FriendlyButton:
        button = FriendlyButton(parent, **kwargs)
        self.cursor_manager.attach(button)
        return button

    def _save_stats(self) -> None:
        try:
            save_stats(self.stats, self.stats_path)
        except OSError:
            self.status_var.set(
                "Stats could not be saved. The board is keeping a dramatic secret."
            )

    def _refresh_player_stats(self) -> None:
        fewest = (
            str(self.stats.fewest_pegs_remaining)
            if self.stats.fewest_pegs_remaining is not None
            else "None yet"
        )
        best_score = str(self.stats.best_score) if self.stats.games_played else "None yet"
        if self.stats.games_played:
            win_rate = round((self.stats.wins / self.stats.games_played) * 100)
            win_text = f"{self.stats.wins} wins ({win_rate}%)"
        else:
            win_text = "No games yet"
        self.player_stats_var.set(
            f"Games played: {self.stats.games_played}\n"
            f"Wins: {win_text}\n"
            f"Best score: {best_score}\n"
            f"Fewest pegs: {fewest}"
        )

    def _maybe_show_tutorial(self) -> None:
        if not self.stats.tutorial_dismissed:
            self._show_tutorial(force=False)

    def _show_tutorial(self, force: bool = True) -> None:
        if self.tutorial_window is not None and self.tutorial_window.winfo_exists():
            self.tutorial_window.lift()
            return

        self.tutorial_window = tk.Toplevel(self.root)
        window = self.tutorial_window
        window.title("How to Play")
        window.configure(bg="#111410")
        window.resizable(False, False)
        window.transient(self.root)
        if not force:
            window.grab_set()

        content = tk.Frame(window, bg="#fff8ea", padx=34, pady=28)
        content.grid(row=0, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        tk.Label(
            content,
            text="How to Play",
            bg="#fff8ea",
            fg="#1d130a",
            font=("Helvetica", 26, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        tk.Message(
            content,
            text=(
                "Pick one peg to lift out. Then jump a peg over its neighbor "
                "into an empty hole. The jumped peg leaves the board. Keep "
                "jumping until the board runs out of legal moves."
            ),
            bg="#fff8ea",
            fg="#21160d",
            font=("Helvetica", 14),
            width=470,
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        example = tk.Canvas(
            content,
            width=470,
            height=126,
            bg="#fff8ea",
            highlightthickness=0,
            bd=0,
        )
        example.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        self._draw_tutorial_example(example)

        tk.Message(
            content,
            text=(
                "Goal: finish with one peg. Getting that last peg back into "
                "the very first empty hole is the tiny wooden jackpot."
            ),
            bg="#fff8ea",
            fg="#5a2b0e",
            font=("Helvetica", 13, "bold"),
            width=470,
        ).grid(row=3, column=0, sticky="w", pady=(0, 18))

        button_row = tk.Frame(content, bg="#fff8ea")
        button_row.grid(row=4, column=0, sticky="ew")
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)
        self._make_button(
            button_row,
            text="Start Playing",
            command=self._close_tutorial,
            width=220,
            bg="#fff8ea",
            fill="#1d130a",
            hover_fill="#332214",
            active_fill="#4c321d",
            text_color="#fff8ea",
            outline="#d7aa63",
            height=54,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._make_button(
            button_row,
            text="Do not show again",
            command=self._dismiss_tutorial,
            width=220,
            bg="#fff8ea",
            fill="#f4d9a9",
            hover_fill="#ffeecb",
            active_fill="#e7bd72",
            text_color="#1d130a",
            outline="#b5792f",
            height=54,
        ).grid(row=0, column=1, sticky="ew", padx=(10, 0))

        self._position_modal(window)
        self.cursor_manager.register_window(window)
        window.protocol("WM_DELETE_WINDOW", self._close_tutorial)

    def _draw_tutorial_example(self, canvas: tk.Canvas) -> None:
        canvas.delete("all")
        width = 470
        height = 126
        canvas.create_rectangle(10, 12, width - 10, height - 12, fill="#d69b55", outline="")
        canvas.create_rectangle(14, 16, width - 14, height - 16, outline="#7a3c16", width=3)
        points = [(110, 66), (235, 66), (360, 66)]
        for x, y in points:
            canvas.create_oval(x - 25, y - 20, x + 25, y + 25, fill="#261409", outline="#9b5a2c", width=2)
            canvas.create_oval(x - 17, y - 14, x + 17, y + 19, fill="#120b07", outline="")
        for x, y in (points[0], points[1]):
            canvas.create_oval(x - 22, y + 8, x + 22, y + 26, fill="#1d120a", outline="", stipple="gray50")
            canvas.create_oval(x - 22, y - 22, x + 22, y + 22, fill="#eee8dc", outline="#9b5a2c", width=2)
            canvas.create_oval(x - 15, y - 15, x + 15, y + 15, fill="#fffaf0", outline="#c3b8a9")
            canvas.create_oval(x - 7, y - 8, x + 8, y + 8, fill="#ffffff", outline="")
        canvas.create_line(156, 66, 320, 66, fill="#1d65c9", width=5, arrow=tk.LAST, arrowshape=(14, 18, 7), capstyle=tk.ROUND)
        canvas.create_text(235, 32, text="jump over", fill="#5a2b0e", font=("Helvetica", 12, "bold"))

    def _dismiss_tutorial(self) -> None:
        self.stats.tutorial_dismissed = True
        self._save_stats()
        self._close_tutorial()

    def _close_tutorial(self) -> None:
        if self.tutorial_window is None:
            return
        if self.tutorial_window.winfo_exists():
            self.cursor_manager.unregister_window(self.tutorial_window)
            self.tutorial_window.destroy()
        self.tutorial_window = None

    def _show_settings(self) -> None:
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.cursor_manager.unregister_window(self.settings_window)
            self.settings_window.destroy()
            self.settings_window = None

        self.settings_window = tk.Toplevel(self.root)
        window = self.settings_window
        window.title("Settings")
        window.configure(bg="#111410")
        window.resizable(False, False)
        window.transient(self.root)

        content = tk.Frame(window, bg="#fff8ea", padx=34, pady=28)
        content.grid(row=0, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        tk.Label(
            content,
            text="Settings",
            bg="#fff8ea",
            fg="#1d130a",
            font=("Helvetica", 26, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        tk.Message(
            content,
            text=(
                "Tune the table without making the pegs fill out paperwork."
            ),
            bg="#fff8ea",
            fg="#21160d",
            font=("Helvetica", 14),
            width=470,
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        controls = tk.Frame(content, bg="#fff8ea")
        controls.grid(row=2, column=0, sticky="ew", pady=(0, 18))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        sound_text = "Sound: On" if self.stats.sound_enabled else "Sound: Off"
        cursor_text = (
            "Cursor: Custom"
            if self.stats.cursor_mode == "auto"
            else "Cursor: System"
        )
        speed_text = f"Speed: {self.stats.animation_speed.title()}"

        self._make_button(
            controls,
            text=sound_text,
            command=self._toggle_sound_setting,
            width=220,
            bg="#fff8ea",
            height=52,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 12))
        self._make_button(
            controls,
            text=speed_text,
            command=self._cycle_animation_speed,
            width=220,
            bg="#fff8ea",
            height=52,
        ).grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 12))
        self._make_button(
            controls,
            text=cursor_text,
            command=self._toggle_cursor_mode,
            width=220,
            bg="#fff8ea",
            height=52,
        ).grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self._make_button(
            controls,
            text="How to Play",
            command=lambda: self._show_tutorial(force=True),
            width=220,
            bg="#fff8ea",
            height=52,
        ).grid(row=1, column=1, sticky="ew", padx=(10, 0))

        tk.Message(
            content,
            text=(
                "Cursor note: Custom mode uses the game pointer where the "
                "platform allows it. System mode keeps the regular arrow if "
                "macOS decides to be precious about cursors."
            ),
            bg="#fff8ea",
            fg="#5a2b0e",
            font=("Helvetica", 12, "bold"),
            width=470,
        ).grid(row=3, column=0, sticky="w", pady=(0, 18))

        self._make_button(
            content,
            text="Done",
            command=self._close_settings,
            width=470,
            bg="#fff8ea",
            fill="#1d130a",
            hover_fill="#332214",
            active_fill="#4c321d",
            text_color="#fff8ea",
            outline="#d7aa63",
            height=54,
        ).grid(row=4, column=0, sticky="ew")

        self._position_modal(window)
        self.cursor_manager.register_window(window)
        window.protocol("WM_DELETE_WINDOW", self._close_settings)

    def _close_settings(self) -> None:
        if self.settings_window is None:
            return
        if self.settings_window.winfo_exists():
            self.cursor_manager.unregister_window(self.settings_window)
            self.settings_window.destroy()
        self.settings_window = None

    def _toggle_sound_setting(self) -> None:
        self.stats.sound_enabled = not self.stats.sound_enabled
        self.sound.enabled = self.stats.sound_enabled
        self._save_stats()
        self._show_settings()

    def _cycle_animation_speed(self) -> None:
        try:
            current_index = ANIMATION_SPEEDS.index(self.stats.animation_speed)
        except ValueError:
            current_index = ANIMATION_SPEEDS.index("normal")
        self.stats.animation_speed = ANIMATION_SPEEDS[
            (current_index + 1) % len(ANIMATION_SPEEDS)
        ]
        self._save_stats()
        self._show_settings()

    def _toggle_cursor_mode(self) -> None:
        self.stats.cursor_mode = (
            "system" if self.stats.cursor_mode == "auto" else "auto"
        )
        self.cursor_manager.set_mode(self.stats.cursor_mode)
        self._save_stats()
        self._show_settings()

    def _animation_delay(self, base_ms: int) -> int:
        multiplier = {
            "relaxed": 1.35,
            "normal": 1.0,
            "quick": 0.65,
        }.get(self.stats.animation_speed, 1.0)
        return max(1, round(base_ms * multiplier))

    def _position_modal(self, window: tk.Toplevel) -> None:
        window.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (
            window.winfo_width() // 2
        )
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - (
            window.winfo_height() // 2
        )
        window.geometry(f"+{max(0, x)}+{max(0, y)}")

    def new_game(self) -> None:
        self._close_game_over()
        self._cancel_animation()
        rows = self._safe_rows()
        self.rows_var.set(rows)
        if hasattr(self, "row_selector"):
            self.row_selector.set_value(rows)
        self.game = TrianglePegSolitaire(rows=rows)
        self.history.clear()
        self.selected_peg = None
        self.hovered_hole = None
        self.hint_move = None
        self.session_score = 0
        self.last_stats_update = None
        self.status_var.set("Pick one white peg to remove and begin.")
        self._update_stats()
        self._draw_board()

    def undo(self) -> None:
        self._cancel_animation()
        if not self.history:
            self.status_var.set("Nothing to undo. The board is already innocent.")
            self.sound.play("invalid")
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
        self.sound.play("slot")
        self._update_stats()
        self._draw_board()

    def show_hint(self) -> None:
        moves = self.game.possible_moves()
        if not moves:
            self.status_var.set("No moves left. The board has closed its case.")
            self.sound.play("invalid")
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

    def _on_rows_changed(self, rows: int) -> None:
        rows = min(MAX_ROWS, max(MIN_ROWS, rows))
        self.rows_var.set(rows)
        self.status_var.set(f"Rows set to {rows}. Press New Game to apply.")
        self.sound.play("pickup")

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

    def _on_canvas_enter(self, event: tk.Event[tk.Canvas]) -> None:
        self.hovered_hole = self._hole_at(event.x, event.y)
        if self.hovered_hole is not None:
            self._draw_board()

    def _on_canvas_leave(self, _event: tk.Event[tk.Canvas]) -> None:
        previous_hover = self.hovered_hole
        self.hovered_hole = None
        if previous_hover is not None:
            self._draw_board()

    def _on_motion(self, event: tk.Event[tk.Canvas]) -> None:
        index = self._hole_at(event.x, event.y)
        if index != self.hovered_hole:
            self.hovered_hole = index
            self._draw_board()

    def _on_board_click(self, event: tk.Event[tk.Canvas]) -> None:
        if self.is_animating:
            return

        index = self._hole_at(event.x, event.y)
        if index is None:
            return

        if self.game.starting_empty is None:
            if self.game.pegs[index] == 1:
                self._save_history()
                self._start_starting_peg_lift(index)
            return

        if not self.game.has_moves():
            self.status_var.set("This round is finished. Start a new board.")
            self.sound.play("invalid")
            return

        if self.selected_peg is None:
            self._select_peg(index)
            return

        if index == self.selected_peg:
            self.selected_peg = None
            self.hint_move = None
            self.sound.play("slot")
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
            self.sound.play("invalid")
            return

        self.selected_peg = index
        self.hint_move = None
        self.sound.play("pickup")
        self.status_var.set(f"Peg {index} selected. Choose an empty landing hole.")
        self._draw_board()

    def _try_move(self, start: int, end: int) -> None:
        try:
            move = self.game.validate_move(start, end)
        except InvalidMove as exc:
            self.status_var.set(f"{exc} The board is strict, but fair.")
            self.sound.play("invalid")
            self._draw_board()
            return

        self._save_history()
        self._start_move_animation(move)

    def _finish_move(self, move: Move) -> None:
        self.game.apply_move(move.start, move.end)
        self.selected_peg = None
        self.hint_move = None
        self.animation_move = None
        self.animation_position = None
        self.removed_peg_animation_position = None
        self.removed_peg_lift_progress = 0.0
        self.animation_hidden_indexes.clear()
        self.is_animating = False
        self.sound.play("slot")

        if self.game.has_moves():
            self.status_var.set(
                f"Nice jump: {move.start} over {move.over} into {move.end}."
            )
        else:
            score = score_board(self.game.pegs, self.game.starting_empty)
            self.session_score += score.points
            stats_update = record_game(
                self.stats,
                rows=self.game.rows,
                score=score.points,
                pegs_remaining=self.game.remaining_pegs,
                is_win=score.is_win,
            )
            self.last_stats_update = stats_update
            self._save_stats()
            self.status_var.set(f"{score.title} {score.message}")
            if stats_update.has_record:
                self.status_var.set(
                    f"{score.title} {score.message} New record, by the way."
                )
            self.sound.play("game_over")
            self.root.after(190, lambda: self._show_game_over(score, stats_update))

        self._update_stats()
        self._draw_board()

    def _start_move_animation(self, move: Move) -> None:
        self._cancel_animation()
        start_x, start_y, radius = self.hole_positions[move.start]
        over_x, over_y, over_radius = self.hole_positions[move.over]
        self.is_animating = True
        self.animation_move = move
        self.animation_hidden_indexes = {move.start, move.over}
        self.animation_position = (start_x, start_y, radius)
        self.removed_peg_animation_position = (over_x, over_y, over_radius)
        self.removed_peg_lift_progress = 0.0
        self.status_var.set(
            f"Moving peg {move.start} over {move.over} into hole {move.end}..."
        )
        self._animate_move_step(move, frame=0)

    def _animate_move_step(self, move: Move, frame: int) -> None:
        if not self.is_animating or self.animation_move != move:
            return

        total_frames = 22
        start_x, start_y, radius = self.hole_positions[move.start]
        end_x, end_y, _radius = self.hole_positions[move.end]
        over_x, over_y, over_radius = self.hole_positions[move.over]
        progress = min(1.0, frame / total_frames)
        eased = 1.0 - ((1.0 - progress) ** 3)
        lift = math.sin(math.pi * progress) * radius * 0.72
        slot_drop = max(0.0, progress - 0.82) / 0.18
        x = start_x + ((end_x - start_x) * eased)
        y = start_y + ((end_y - start_y) * eased) - lift + (slot_drop * radius * 0.22)
        scale = 1.08 + (math.sin(math.pi * progress) * 0.18) - (slot_drop * 0.08)
        self.animation_position = (x, y, radius * scale)

        remove_progress = min(1.0, progress / 0.96)
        remove_eased = 1.0 - ((1.0 - remove_progress) ** 3)
        remove_lift = remove_eased * over_radius * 4.15
        if remove_progress < 0.72:
            remove_scale = 1.03 + (math.sin(remove_progress * math.pi) * 0.14)
        else:
            vanish_progress = (remove_progress - 0.72) / 0.28
            remove_scale = max(0.0, 1.05 * ((1.0 - vanish_progress) ** 2.0))

        self.removed_peg_lift_progress = remove_progress
        if remove_scale <= 0.08:
            self.removed_peg_animation_position = None
        else:
            self.removed_peg_animation_position = (
                over_x,
                over_y - remove_lift,
                over_radius * remove_scale,
            )
        self._draw_board()

        if frame >= total_frames:
            self.animation_after_id = None
            self._finish_move(move)
            return

        self.animation_after_id = self.root.after(
            self._animation_delay(15),
            lambda: self._animate_move_step(move, frame + 1),
        )

    def _start_starting_peg_lift(self, index: int) -> None:
        self._cancel_animation()
        x, y, radius = self.hole_positions[index]
        self.is_animating = True
        self.animation_hidden_indexes = {index}
        self.animation_position = (x, y, radius)
        self.sound.play("lift")
        self.status_var.set(f"Lifting peg {index} out of the board...")
        self._animate_starting_lift_step(index, frame=0)

    def _animate_starting_lift_step(self, index: int, frame: int) -> None:
        if not self.is_animating or index not in self.animation_hidden_indexes:
            return

        total_frames = 24
        x, y, radius = self.hole_positions[index]
        progress = min(1.0, frame / total_frames)
        eased = 1.0 - ((1.0 - progress) ** 3)
        wobble = math.sin(progress * math.pi * 5) * radius * 0.055 * (1.0 - progress)
        lift = eased * radius * 2.55
        scale = max(0.12, 1.08 + (math.sin(progress * math.pi) * 0.28) - progress)
        self.animation_position = (x + wobble, y - lift, radius * scale)
        self._draw_board()

        if frame >= total_frames:
            self.animation_after_id = None
            self._finish_starting_peg_lift(index)
            return

        self.animation_after_id = self.root.after(
            self._animation_delay(14),
            lambda: self._animate_starting_lift_step(index, frame + 1),
        )

    def _finish_starting_peg_lift(self, index: int) -> None:
        self.game.remove_starting_peg(index)
        self.selected_peg = None
        self.hint_move = None
        self.animation_move = None
        self.animation_position = None
        self.removed_peg_animation_position = None
        self.removed_peg_lift_progress = 0.0
        self.animation_hidden_indexes.clear()
        self.is_animating = False
        self.status_var.set(
            "Good. The first peg has left the building. "
            "Now jump a peg into an empty hole."
        )
        self._update_stats()
        self._draw_board()

    def _cancel_animation(self) -> None:
        if self.animation_after_id is not None:
            try:
                self.root.after_cancel(self.animation_after_id)
            except tk.TclError:
                pass
        self.animation_after_id = None
        self.animation_move = None
        self.animation_position = None
        self.removed_peg_animation_position = None
        self.removed_peg_lift_progress = 0.0
        self.animation_hidden_indexes.clear()
        self.is_animating = False

    def _update_stats(self) -> None:
        self.score_var.set(f"Score: {self.session_score}")
        self.pegs_var.set(f"Pegs remaining: {self.game.remaining_pegs}")

        if self.game.starting_empty is None:
            self.moves_var.set("Moves available: choose a starting peg")
        else:
            move_count = self.game.possible_move_count()
            label = "move" if move_count == 1 else "moves"
            self.moves_var.set(f"Moves available: {move_count} {label}")
        self._refresh_player_stats()

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
        self._draw_animation_pegs()
        self.cursor_manager.redraw(self.canvas)

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

        if self.wood_texture is None:
            self._draw_procedural_grain()
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
        for line_number in range(16):
            y = top + ((line_number + 1) * height / 18)
            wave = ((line_number % 5) - 2) * 1.4
            color = ("#704014", "#8a551f", "#b87935", "#d59a51")[line_number % 4]
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
            hovered = index == self.hovered_hole

            self._draw_hole(
                index,
                x,
                y,
                radius,
                destination=destination,
                hinted=hinted,
                hovered=hovered,
            )

        for index, (x, y, radius) in self.hole_positions.items():
            if index in self.animation_hidden_indexes:
                continue
            selected = index == self.selected_peg
            hinted = index in hint_positions
            hovered = index == self.hovered_hole
            if self.game.pegs[index] == 1:
                self._draw_white_peg(
                    x,
                    y - (radius * 0.18 if selected else 0),
                    radius,
                    selected=selected,
                    hinted=hinted,
                    hovered=hovered,
                    lifted=selected,
                )

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
        index: int,
        x: float,
        y: float,
        radius: float,
        *,
        destination: bool,
        hinted: bool,
        hovered: bool,
    ) -> None:
        self.canvas.create_oval(
            x - radius * 1.08,
            y - radius * 0.92,
            x + radius * 1.08,
            y + radius * 1.18,
            fill="#261409",
            outline="#9b5a2c",
            width=2,
            tags=("hole", "hole_outer", f"hole_{index}"),
        )
        self.canvas.create_oval(
            x - radius * 0.78,
            y - radius * 0.68,
            x + radius * 0.78,
            y + radius * 0.82,
            fill="#120b07",
            outline="#100906",
            width=1,
            tags=("hole", "hole_inner", f"hole_{index}"),
        )

        if destination or hinted or hovered:
            ring_color = "#fff3c2" if destination or hinted else "#f3c887"
            self.canvas.create_oval(
                x - radius * 1.34,
                y - radius * 1.20,
                x + radius * 1.34,
                y + radius * 1.46,
                outline=ring_color,
                width=3,
                tags=("hole_highlight", f"hole_{index}"),
            )

    def _draw_white_peg(
        self,
        x: float,
        y: float,
        radius: float,
        *,
        selected: bool,
        hinted: bool,
        hovered: bool = False,
        lifted: bool = False,
        draw_shadow: bool = True,
        tags: str | tuple[str, ...] = (),
    ) -> None:
        peg_radius = radius * 0.92
        shadow_width = 1.32 if lifted else 1.08
        shadow_height = 0.68 if lifted else 0.46
        shadow_y = y + peg_radius * (0.58 if lifted else 0.48)
        if draw_shadow:
            self.canvas.create_oval(
                x - peg_radius * shadow_width,
                shadow_y - peg_radius * shadow_height,
                x + peg_radius * shadow_width,
                shadow_y + peg_radius * shadow_height,
                fill="#1d120a",
                outline="",
                stipple="gray50",
                tags=tags,
            )
        self.canvas.create_oval(
            x - peg_radius * 0.98,
            y - peg_radius * 0.88,
            x + peg_radius * 0.98,
            y + peg_radius * 1.00,
            fill="#9b5a2c",
            outline="#5b2d13",
            width=2,
            tags=tags,
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
                tags=tags,
            )

        self.canvas.create_oval(
            x - peg_radius * 0.48,
            y - peg_radius * 0.58,
            x - peg_radius * 0.04,
            y - peg_radius * 0.18,
            fill="#ffffff",
            outline="",
            tags=tags,
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
            tags=tags,
        )

        if selected or hinted or hovered:
            ring_color = "#fff3c2" if selected or hinted else "#f7d48b"
            self.canvas.create_oval(
                x - peg_radius * 1.22,
                y - peg_radius * 1.22,
                x + peg_radius * 1.22,
                y + peg_radius * 1.22,
                outline=ring_color,
                width=4,
                tags=tags,
            )

    def _draw_animation_pegs(self) -> None:
        if self.removed_peg_animation_position is not None:
            x, y, radius = self.removed_peg_animation_position
            if self.animation_move is not None:
                over_x, over_y, over_radius = self.hole_positions[self.animation_move.over]
                self._draw_lift_shadow(
                    over_x,
                    over_y,
                    over_radius,
                    self.removed_peg_lift_progress,
                )
            self._draw_white_peg(
                x,
                y,
                radius,
                selected=False,
                hinted=False,
                hovered=False,
                lifted=True,
                draw_shadow=False,
                tags="removed_peg_animation",
            )

        if self.animation_position is None:
            return

        x, y, radius = self.animation_position
        self._draw_white_peg(
            x,
            y,
            radius,
            selected=True,
            hinted=False,
            hovered=False,
            lifted=True,
            tags="animation_peg",
        )

    def _draw_lift_shadow(
        self,
        x: float,
        y: float,
        radius: float,
        progress: float,
    ) -> None:
        peg_radius = radius * 0.92
        shadow_scale = max(0.22, 1.0 - (progress * 0.72))
        shadow_width = 1.08 * shadow_scale
        shadow_height = 0.46 * shadow_scale
        shadow_y = y + peg_radius * 0.48
        stipple = "gray50" if progress < 0.58 else "gray25"
        self.canvas.create_oval(
            x - peg_radius * shadow_width,
            shadow_y - peg_radius * shadow_height,
            x + peg_radius * shadow_width,
            shadow_y + peg_radius * shadow_height,
            fill="#1d120a",
            outline="",
            stipple=stipple,
            tags="removed_peg_shadow",
        )

    def _hole_at(self, x: float, y: float) -> int | None:
        for index, (hole_x, hole_y, radius) in self.hole_positions.items():
            dx = x - hole_x
            dy = y - hole_y
            if (dx * dx) + (dy * dy) <= (radius * 1.25) ** 2:
                return index
        return None

    def _show_game_over(
        self,
        score: ScoreResult,
        stats_update: StatsUpdate | None = None,
    ) -> None:
        self._close_game_over()
        self.game_over_window = tk.Toplevel(self.root)
        window = self.game_over_window
        window.title("Game Over")
        window.configure(bg="#111410")
        window.resizable(False, False)
        window.transient(self.root)
        window.grab_set()

        content = tk.Frame(window, bg="#fff8ea", padx=34, pady=30)
        content.grid(row=0, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        tk.Label(
            content,
            text="Game Over",
            bg="#fff8ea",
            fg="#1d130a",
            font=("Helvetica", 28, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        tk.Label(
            content,
            text=score.title,
            bg="#fff8ea",
            fg="#5a2b0e",
            font=("Helvetica", 18, "bold"),
            wraplength=440,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))
        tk.Message(
            content,
            text=score.message,
            bg="#fff8ea",
            fg="#21160d",
            font=("Helvetica", 14),
            width=440,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 20))

        if stats_update is not None and stats_update.has_record:
            record_text = "New record! The board is pretending to stay humble."
        elif stats_update is not None and stats_update.is_win:
            record_text = "A clean win. The pegs are absolutely taking notes."
        else:
            record_text = "Another one for the tiny wooden history books."
        tk.Label(
            content,
            text=record_text,
            bg="#fff8ea",
            fg="#7a3c16",
            font=("Helvetica", 14, "bold"),
            wraplength=440,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 14))

        stats = [
            ("Round points", str(score.points)),
            ("Total score", str(self.session_score)),
            ("Pegs remaining", str(self.game.remaining_pegs)),
            ("Starting hole", str(self.game.starting_empty)),
            ("Moves left", str(self.game.possible_move_count())),
            ("Games played", str(self.stats.games_played)),
            ("Wins", str(self.stats.wins)),
            ("Best score", str(self.stats.best_score)),
            (
                "Fewest pegs",
                str(self.stats.fewest_pegs_remaining)
                if self.stats.fewest_pegs_remaining is not None
                else "None yet",
            ),
        ]
        stats_box = tk.Frame(
            content,
            bg="#ffffff",
            highlightbackground="#d7aa63",
            highlightthickness=2,
            padx=16,
            pady=12,
        )
        stats_box.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        stats_box.columnconfigure(0, weight=1)
        for row, (label, value) in enumerate(stats):
            tk.Label(
                stats_box,
                text=label,
                bg="#ffffff",
                fg="#4a3828",
                font=("Helvetica", 13, "bold"),
            ).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 34))
            tk.Label(
                stats_box,
                text=value,
                bg="#ffffff",
                fg="#111410",
                font=("Helvetica", 13, "bold"),
            ).grid(row=row, column=1, sticky="e", pady=3)

        button_row = tk.Frame(content, bg="#fff8ea")
        button_row.grid(row=5, column=0, columnspan=2, sticky="ew")
        button_row.columnconfigure(0, weight=1, minsize=220)
        button_row.columnconfigure(1, weight=1, minsize=220)
        self._make_button(
            button_row,
            text="New Game",
            command=self.new_game,
            width=220,
            bg="#111410",
            fill="#1d130a",
            hover_fill="#332214",
            active_fill="#4c321d",
            text_color="#fff8ea",
            outline="#d7aa63",
            height=54,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._make_button(
            button_row,
            text="Review Board",
            command=self._close_game_over,
            width=220,
            bg="#fff8ea",
            fill="#f4d9a9",
            hover_fill="#ffeecb",
            active_fill="#e7bd72",
            text_color="#1d130a",
            outline="#b5792f",
            height=54,
        ).grid(row=0, column=1, sticky="ew", padx=(10, 0))

        self._position_modal(window)
        self.cursor_manager.register_window(window)
        window.protocol("WM_DELETE_WINDOW", self._close_game_over)

    def _close_game_over(self) -> None:
        if self.game_over_window is None:
            return
        if self.game_over_window.winfo_exists():
            self.cursor_manager.unregister_window(self.game_over_window)
            self.game_over_window.destroy()
        self.game_over_window = None


def main() -> None:
    root = tk.Tk()
    PegSolitaireApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
