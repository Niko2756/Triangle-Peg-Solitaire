"""Console interface for Triangle Peg Solitaire."""

from __future__ import annotations

from pathlib import Path

from .game import MIN_ROWS, InvalidMove, Move, TrianglePegSolitaire, score_board


YES_VALUES = {"yes", "y"}
NO_VALUES = {"no", "n"}
NO_USERNAME = "NOUSERNAMEZ"


def main() -> None:
    print("Triangle Peg Solitaire")
    print("Coded by Niko. Lightly polished, still full of personality.\n")

    points, user_name = load_previous_score()
    while True:
        game = create_game()
        points = play_round(game, points)

        if ask_yes_no("\nDo you want to end this program?", default=False):
            save_score(points, user_name)
            print("Thank you so much for playing. This game was coded by Niko.")
            break

        print("\nNew board, new choices, same tiny pegs judging silently.\n")


def create_game() -> TrianglePegSolitaire:
    rows = ask_rows()
    game = TrianglePegSolitaire(rows=rows)
    print_board(game)

    starting_peg = ask_int(
        "Pick the one peg to remove: ",
        minimum=0,
        maximum=game.total_holes - 1,
    )
    game.remove_starting_peg(starting_peg)
    print_board(game)
    return game


def play_round(game: TrianglePegSolitaire, points: list[int]) -> list[int]:
    while game.has_moves():
        move = ask_move(game)
        game.apply_move(move.start, move.end)
        print_board(game)
        possible_moves = game.possible_move_count()
        print(
            f"{possible_moves} possible move "
            f"{'choice' if possible_moves == 1 else 'choices'} remaining."
        )

    print("\nThere are no more possible moves.\n")
    score = score_board(game.pegs, game.starting_empty)
    points.append(score.points)
    print(score.title)
    print(score.message)
    print(f"You get {score.points} points.\n")
    print(f"The score of your previous game was: {points[-2]}")
    print(f"Your current total score is: {sum(points)}")
    return points


def ask_move(game: TrianglePegSolitaire) -> Move:
    while True:
        start = ask_peg_to_move(game)
        while True:
            end = ask_hole_to_land_in(game)
            try:
                return game.validate_move(start, end)
            except InvalidMove as exc:
                print("\nYou have attempted a move that is not permitted.")
                print(f"{exc}\n")
                if ask_yes_no(
                    "Do you want to reselect the landing hole? "
                    "Say no to choose a different peg.",
                    default=True,
                ):
                    continue
                break


def ask_peg_to_move(game: TrianglePegSolitaire) -> int:
    while True:
        selected = ask_int(
            "Pick the one peg to move: ",
            minimum=0,
            maximum=game.total_holes - 1,
        )
        if game.pegs[selected] == 1:
            return selected
        print("There is no peg there. Please select a hole with a peg.")


def ask_hole_to_land_in(game: TrianglePegSolitaire) -> int:
    while True:
        selected = ask_int(
            "Pick the hole to move your selected peg to: ",
            minimum=0,
            maximum=game.total_holes - 1,
        )
        if game.pegs[selected] == 0:
            return selected
        print("Please select a hole without a peg.")


def ask_rows() -> int:
    while True:
        rows = ask_int(
            "How many rows do you want to play? Press Enter for default: ",
            default=5,
        )
        if rows >= MIN_ROWS:
            return rows
        print("Any board below 4 rows is not solvable.")


def ask_int(
    prompt: str,
    *,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    while True:
        raw_value = input(prompt).strip()
        if raw_value == "" and default is not None:
            return default
        try:
            value = int(raw_value)
        except ValueError:
            print(
                "Hey, I don't think that's even a number. Go ahead and try "
                "again, but make it an actual number this time.\n"
            )
            continue

        if minimum is not None and value < minimum:
            print_range_message(minimum, maximum)
            continue
        if maximum is not None and value > maximum:
            print_range_message(minimum, maximum)
            continue
        return value


def ask_yes_no(prompt: str, *, default: bool | None = None) -> bool:
    if default is True:
        suffix = "Enter yes or no, or press Enter for yes"
    elif default is False:
        suffix = "Enter yes or no, or press Enter for no"
    else:
        suffix = "Enter yes or no"

    while True:
        answer = input(f"{prompt} ({suffix}): ").strip().lower()
        if answer == "" and default is not None:
            return default
        if answer in YES_VALUES:
            return True
        if answer in NO_VALUES:
            return False
        print(
            "Come on, that's not what I asked for. Please give me an "
            "affirmative yes or a no in English, please."
        )


def print_range_message(minimum: int | None, maximum: int | None) -> None:
    if minimum is not None and maximum is not None:
        print(f"Please enter a peg between {minimum} and {maximum}.")
    elif minimum is not None:
        print(f"Please enter a number that is at least {minimum}.")
    elif maximum is not None:
        print(f"Please enter a number that is no more than {maximum}.")


def print_board(game: TrianglePegSolitaire) -> None:
    print()
    print_triangle(game.rows_as_values())
    print()
    print_triangle(game.rows_as_indexes())
    print()


def print_triangle(rows: list[list[int]]) -> None:
    cell_width = max(1, len(str(rows[-1][-1])))
    rendered_rows = [
        " ".join(f"{value:>{cell_width}}" for value in row) for row in rows
    ]
    width = len(rendered_rows[-1])
    for row in rendered_rows:
        print(row.center(width))


def load_previous_score() -> tuple[list[int], str]:
    if not ask_yes_no(
        "\nDo you want to load your score from a previous game session?",
        default=False,
    ):
        return [0], NO_USERNAME

    user_name = input_name()
    score_file = score_path(user_name)
    try:
        points = [
            int(line.strip())
            for line in score_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except FileNotFoundError:
        print(
            "I could not find that score file, so we are starting fresh. "
            "Mysterious, but survivable."
        )
        return [0], user_name
    except ValueError:
        print(
            "That score file has something weird in it. We are starting fresh "
            "before the math starts making threats."
        )
        return [0], user_name

    if not points:
        points = [0]
    print(f"Your score has been loaded from: {score_file.name}")
    return points, user_name


def save_score(points: list[int], user_name: str) -> None:
    if not ask_yes_no("\nDo you want to save your score for later?", default=False):
        print("You have decided not to save your score.")
        return

    if user_name == NO_USERNAME:
        user_name = input_name()

    score_file = score_path(user_name)
    score_file.write_text(
        "".join(f"{point}\n" for point in points),
        encoding="utf-8",
    )
    print(f"Your score has been saved under: {score_file.name}")


def input_name() -> str:
    while True:
        user_name = input("Enter your name: ").strip()
        if (
            not user_name
            or not user_name.isprintable()
            or user_name.upper() == NO_USERNAME
        ):
            print(
                "Come on, that's not what I asked for. Please give me a name "
                "in English, please.\n"
            )
            continue
        return " ".join(part.capitalize() for part in user_name.split())


def score_path(user_name: str) -> Path:
    safe_name = "".join(
        character
        for character in user_name
        if character.isalnum() or character in (" ", "_", "-")
    ).strip()
    if not safe_name:
        safe_name = "Player"
    return Path(f"{safe_name}'s Peg Solitaire Score.txt")


if __name__ == "__main__":
    main()
