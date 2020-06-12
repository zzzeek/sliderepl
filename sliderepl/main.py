from argparse import ArgumentParser
import os
import sys

from sliderepl import Deck


def main(argv=None, **kwargs):

    if sys.platform == "win32":
        color_default = "never"
    else:
        color_default = "auto"

    parser = ArgumentParser()

    parser.add_argument("script", type=str, help="script file to run")
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Execute all slides without prompting and exit.",
    )
    parser.add_argument(
        "-p", "--presentation", action="store_true", help="Presentation mode"
    )
    parser.add_argument("--timer", action="store_true", help="Show timer")
    parser.add_argument(
        "-q",
        "--quick",
        action="store_true",
        default=True,
        help="'Enter' key is a shortcut for 'next'",
    )
    parser.add_argument(
        "-s",
        "--short",
        action="store_true",
        default=False,
        help="Run the 'short' version of the slides "
        "(skip those with 'l' flag)",
    )
    parser.add_argument(
        "--color",
        dest="color",
        default=color_default,
        choices=("never", "auto", "light", "dark"),
        help=(
            "Control the use of color syntax highlighting. "
            "Choices are 'never', 'auto', 'light' and 'dark'."
        ),
    )

    options = parser.parse_args(argv)
    deck = None
    if os.path.exists("_config.py"):
        locals_ = {}
        exec(compile(open("_config.py").read(), "_config.py", "exec"), locals_)
        deck = locals_.get("deck")
    if deck is None:
        deck = Deck
    deck.run(options.script, **vars(options))
