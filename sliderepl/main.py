from argparse import ArgumentParser
import os
from pathlib import Path
import sys

import tomli

from . import Deck
from . import menu


def _load_toml(config_file="pyproject.toml"):

    if os.path.exists(config_file):
        with open(config_file, "rb") as f:
            toml_dict = tomli.load(f)  # type: ignore
    else:
        toml_dict = {}

    return toml_dict.get("tool", {}).get("sliderepl", {})


def main(argv=None, **kwargs):

    if sys.platform == "win32":
        color_default = "never"
    else:
        color_default = "auto"

    parser = ArgumentParser()

    parser.add_argument(
        "script", type=str, help="script file to run", nargs="?"
    )
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
        "--toml-config",
        type=str,
        default="pyproject.toml",
        help="name / path of pyproject.toml file",
    )
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

    toml = _load_toml(options.toml_config)

    slide_location = Path(".") / Path(toml.get("slides", "slides"))
    config = slide_location / Path("_config.py")

    deck = None

    if config.exists():
        locals_ = {}
        exec(config.read_text(), locals_)
        deck = locals_.get("deck")
    if deck is None:
        deck = Deck

    if options.script is None:
        menu.menu(deck, options, slide_location)
    else:
        deck.run(options.script, **vars(options))
