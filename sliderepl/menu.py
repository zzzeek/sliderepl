from argparse import Namespace
from pathlib import Path
import re
import sys

from termcolor import colored as color_text

from . import Deck


def _prompt_text(text):
    return color_text(text, "green")


def _number_text(text):
    return color_text(text, "magenta")


def _header_text(text):
    return color_text(text, "cyan")


class DeckFile:
    def __init__(self, path):
        self.name = path.name
        self.path = path

    def __str__(self):
        return self.name


def menu(deck: Deck, options: Namespace, slides: Path) -> None:
    all_slides = [
        DeckFile(p)
        for p in sorted(
            [
                path
                for path in slides.glob("[!_]*.py")
                if re.match(r"^\d+_", path.name)
            ]
        )
    ]

    while True:
        print("\n\n")
        print(_header_text("Slide Deck"))
        print(_header_text("=========="))
        for idx, filename in enumerate(all_slides, 1):
            print(_number_text(f"[{idx}]"), filename)
            idx += 1
        print(_number_text("[Q]"), "Quit")
        prompt = "\n" + _prompt_text("[enter chapter number]: ")
        try:
            line = input(prompt)
        except EOFError:
            break

        cmd = line.strip().lower()
        if cmd == "q":
            sys.exit()
        elif re.match(r"^\d+$", cmd):
            num = int(cmd)
            if num < 1 or num > len(all_slides):
                print("Invalid slide number")
            else:
                deck.run(all_slides[num - 1].path, **vars(options))
        else:
            print("unknown command")
