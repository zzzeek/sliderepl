# sliderepl
#   Copyright (c) Jason Kirtland <jek@discorporate.us>
#   Copyright (c) Michael Bayer <mike_mp@zzzcomputing.com>
#   sliderepl is released under the MIT License:
#   http://www.opensource.org/licenses/mit-license.php
from __future__ import annotations

import code
import inspect
import os
from pathlib import Path
import re
import sys
import textwrap
import traceback
from typing import Any
from typing import Dict
from typing import MutableMapping
from typing import Optional

try:
    import rlcompleter
    import readline
except ImportError:
    readline = None

if sys.platform == "win32":
    clearcmd = "cls"
else:
    clearcmd = "clear"


environ = None


class ReallyRerun(Exception):
    def __init__(self, slide):
        self.slide = slide


class Deck:
    expose = (
        "next",
        "goto",
        "show",
        "info",
        "prev",
        "rerun",
        "presentation",
        "rreallyrerun",
        "quit",
    )

    _exec_on_return = False

    banner_top = ""

    min_banner_width = 67
    bullet_width = 70

    def __init__(self, path: Optional[Path] = None, **options: Dict[str, Any]):
        self.path = path or "<no file>"
        self.slides = []
        self.current = 0
        self.current_top_slide = 0
        self.init_slide: Optional[Deck.Slide] = None
        self.color = options.get("color", None)
        self.short_pres = options.get("short", False)
        self._set_presentation(options.get("presentation", False))
        self.pending_exec = False
        self._letter_commands = {}
        self._expose_map: Dict[str, Any] = dict(
            (f"!{name}", getattr(self, name)) for name in self.expose
        )

        for name in self.expose:
            short_cmd = f"!{name[0]}"
            if short_cmd in self._expose_map:
                short_cmd = f"!{name[0:2]}"
            self._expose_map[short_cmd] = getattr(self, name)
            self._letter_commands[f"!{name}"] = short_cmd
        self._expose_map["?"] = self.commands

    def setup_environ(self, environ: MutableMapping[str, Any]) -> None:
        pass

    @property
    def highlight_stdout(self):
        return sys.stdout

    @property
    def ps1(self):
        return getattr(sys, "ps1", ">>> ")

    @property
    def ps2(self):
        return getattr(sys, "ps2", "... ")

    def start(self):
        pass

    def _set_presentation(self, mode):
        self._presentation = mode
        print(
            "%% presentation mode is now %s"
            % (self._presentation and "ON" or "OFF")
        )

    def presentation(self):
        """Toggle presentation mode"""
        self._set_presentation(not self._presentation)

    def rerun(self):
        """Re-run the current slide."""

        self.pending_exec = False
        self._do_slide(self.current)

    def rreallyrerun(self):
        """reload the whole deck and come back to this slide"""

        raise ReallyRerun(self.current_top_slide)

    def prev(self):
        """Advance to the previous slide."""

        self.pending_exec = False
        self.current -= 1

        self._do_slide(self.current)

    def next(self):
        """Advance to the next slide."""
        self._next()

    def quit(self):
        """Quit to menu / command prompt"""

        raise EOFError("done")

    def _next(self, run=True):
        """Advance to the next slide."""

        if self.pending_exec:
            self._do_slide(self.current, run=True, echo=False)
            self.pending_exec = False
            return

        if self.current >= len(self.slides):
            print("%% The slideshow is over.")
            return
        self.current += 1

        self._do_slide(self.current, run=run)

    def _do_bullet(self, bullet, *, prompt=True):
        indent = re.match(r"^ +\* ", bullet)
        assert indent is not None
        padding = len(indent.group(0)) * " "

        bullet = "\n".join(
            [
                padding + line if lineno > 0 else line
                for lineno, line in enumerate(
                    textwrap.wrap(bullet, width=self.bullet_width)
                )
            ]
        )

        bullet_tokens = re.match(r"^( +)\* (.*)", bullet, re.S)

        assert bullet_tokens

        bullet = self._color(f"{bullet_tokens.group(1)}\u2022 ", "boldbullet")

        color = "plain"
        for element in re.split(r"(\*\*|``)", bullet_tokens.group(2)):
            if element == "**":
                color = "boldbullet" if color != "boldbullet" else "plain"
            elif element == "``":
                color = "codebullet" if color != "codebullet" else "plain"
            else:
                bullet += self._color(element, color)

        if prompt:
            input(f"{bullet}\n\n")
        else:
            print(f"{bullet}\n\n")

    def _do_slide(self, num, run=True, echo=True):
        slide = self.slides[num - 1]
        if echo:
            if self._presentation:
                if not slide.no_clear:
                    os.system(clearcmd)
                    print(self.banner_top)
                    print(slide._banner())
                    self.current_top_slide = num
                else:
                    print(slide._banner())
            else:
                print(slide._banner())

            if slide.bullets and run != "force":
                last_bullet = slide.bullets[-1]
                has_code = bool(slide.codeblocks)
                for bullet in slide.bullets:
                    self._do_bullet(
                        bullet, prompt=has_code or bullet is not last_bullet
                    )

        slide.run(run=run, echo=echo)
        if run != "force" and slide.no_exec and not slide.never_exec:
            self.pending_exec = True

    def slide_actor(fn):
        def decorated(self, slide_number):
            if isinstance(slide_number, str) and not slide_number.isdigit():
                print("%% Usage: %s slide_number" % fn.__name__)
                return
            num = int(slide_number)
            if num < 1 or num > len(self.slides):
                print(
                    "%% Slide #%s is out of range (1 - %s)."
                    % (num, len(self.slides))
                )
            else:
                return fn(self, num)

        decorated.__doc__ = fn.__doc__
        return decorated

    @slide_actor
    def show(self, slide_number):
        """show slide <number>, display a slide without executing it."""

        self._do_slide(slide_number, False)

    @slide_actor
    def goto(self, slide_number):
        """goto slide <number>"""

        self.pending_exec = False
        if slide_number <= self.current:
            self.current = slide_number
            self._do_slide(self.current)
        else:
            rg = range(slide_number - self.current)
            for _ in rg[0:-1]:
                self._next(run="force")
            self._next()

    def info(self):
        """Display information about this slide deck."""
        print(
            "%% Now at slide %s of %s from deck %s"
            % (self.current, len(self.slides), self.path)
        )

    def commands(self):
        """Display this help message."""
        for cmd in ["?"] + ["!%s" % exp for exp in self.expose]:
            line_start = (
                "% "
                + cmd
                + (
                    cmd in self._letter_commands
                    and " / " + self._letter_commands[cmd]
                    or ""
                )
            )

            space = " " * (25 - len(line_start))
            print(line_start + space + self._expose_map[cmd].__doc__)

    del slide_actor

    class Slide(object):
        no_clear = False
        no_exec = False
        never_exec = False
        no_echo = False
        init = False
        has_bullets = False
        title = None

        def __init__(self, deck, file, index):
            self.deck = deck
            self.codeblocks = []
            self.lines = []
            self.intro = []
            self.bullets = []
            self._stack = []
            self._level = None
            self.file = file
            self.index = index

        def _banner(self):
            banner = ""

            box_size = self.deck.min_banner_width - 4

            if not self.title and not self.intro:
                return banner

            title = None

            if self.title:
                title = "*** " + self.title + " ***"
                title_len = len(title)
                box_size = max(box_size, title_len)
                title = self.deck._color(title, "titletext")
            else:
                title_len = 0

            if self.intro:
                box_size = max(
                    *[box_size]
                    + [len(self.deck._decolorize(l)) for l in self.intro]
                )

            box_size += 4

            if not self.deck._presentation:
                banner += "\n"

            # box_plus = self.deck._color("+", "box")
            box_ul = self.deck._color("\u250C", "box")
            box_ur = self.deck._color("\u2510", "box")
            box_ll = self.deck._color("\u2514", "box")
            box_lr = self.deck._color("\u2518", "box")
            box_ls = self.deck._color("\u251C", "box")
            box_rs = self.deck._color("\u2524", "box")
            box_line = self.deck._color("\u2502", "box")  # |
            box_dash = self.deck._color("\u2500", "box")  # -

            banner += f"{box_ul}%s{box_ur}\n" % (box_dash * (box_size - 1))

            if title or self.intro:
                if title:
                    banner += f"{box_line} %s%s{box_line}\n" % (
                        title,
                        (" " * (box_size - title_len - 2)),
                    )
                    if self.intro:
                        banner += f"{box_ls}%s{box_rs}\n" % (
                            box_dash * (box_size - 1)
                        )

                if self.intro:
                    banner += (
                        "\n".join(
                            f"{box_line} %s%s{box_line}"
                            % (
                                self.deck._color(l, "intro_line"),
                                (
                                    " "
                                    * (
                                        box_size
                                        - len(self.deck._decolorize(l))
                                        - 2
                                    )
                                ),
                            )
                            for l in self.intro
                        )
                        + "\n"
                    )

            index = " (%d / %d) " % (self.index, len(self.deck.slides))

            left_line = box_size - len(index) - 3
            right_line = box_size - left_line - len(index) - 1
            banner += f"{box_ll}%s{box_lr}\n" % (
                (box_dash * (left_line))
                + self.deck._color(index, "slidenum")
                + (box_dash * (right_line))
            )

            return banner

        def run(self, run=True, echo=True):
            if run is True and echo and self.no_exec:
                run = False

            for i, (display, co) in enumerate(self.codeblocks):
                last_block = i == len(self.codeblocks) - 1

                no_echo = self.no_echo
                if echo and not no_echo:
                    shown = []

                    if not run:
                        while not display[-1].strip():
                            display.pop(-1)

                    for j, l in enumerate(display):
                        # this allows for multiline strings in slides
                        # that will display as code, but not actually run
                        # as anything more than a string (and also not be
                        # anything more than a plain string in the source file)
                        if l.strip() == '"""':
                            continue

                        ps1 = self.deck.ps1
                        ps2 = self.deck.ps2

                        if j == 0:
                            to_show = ps1 + l
                        elif (
                            l.startswith(" ")
                            or l.startswith(")")
                            or l.startswith("]")
                        ):
                            to_show = ps2 + l
                        elif not l.isspace():
                            to_show = ps1 + l
                        else:
                            to_show = l

                        to_show = to_show

                        if (
                            not run
                            and not self.never_exec
                            and last_block
                            and j == len(display) - 1
                        ):
                            self.deck._exec_on_return = True

                        shown.append(to_show)

                    Deck._add_history("".join(display).rstrip())
                    shown = "".join(shown)

                    if last_block:
                        shown = shown.rstrip() + "\n"
                    sys.stdout.write(self.deck._highlight_text(shown))

                if run and not self.never_exec:
                    try:
                        exec(co, environ)
                    except:
                        traceback.print_exc()
            if run:
                print("")

        def __str__(self):
            return "".join(self.lines)

        def _append(self, line):
            self.lines.append(line)
            if not self._stack and line.isspace():
                return
            indent = len(line) - len(line.lstrip())
            if not self._stack:
                self._level = indent
            elif indent <= self._level:
                try:
                    co = self._compile()
                    if co:
                        self.codeblocks.append((self._pop(), co))
                except SyntaxError:
                    pass
            self._stack.append(line)

        def _close(self):
            if self._stack:
                co = self._compile()
                assert co
                self.codeblocks.append((self._pop(), co))

            if self.intro:
                while not self.intro[-1].strip():
                    self.intro.pop(-1)

        def _compile(self):
            style = getattr(self, "no_return", False) and "exec" or "single"
            try:
                return code.compile_command(
                    "".join(self._stack), "<input>", style
                )
            except:
                print("code:", "".join(self._stack))
                raise

        def _pop(self):
            self._stack.reverse()
            lines = list(self._stack)
            lines.reverse()
            self._stack = []
            return lines

    @classmethod
    def run(cls, path: Optional[Path] = None, **options):
        """Run an interactive session for a Deck and exit when complete."""
        if path is None:
            path = Path(sys.argv[0])

        _goto = None
        while True:
            deck = cls.from_path(path, **options)
            if not deck:
                sys.stderr.write("Aborting: no slides!\n")
                sys.exit(-1)

            deck.start()

            if options.get("run_all"):
                deck.goto(len(deck.slides))
                sys.exit(0)

            global environ
            environ = {"__name__": "__console__", "__doc__": None}

            # environ['environ'] = environ  # useful for debugging

            console = code.InteractiveConsole(locals=environ)

            deck.setup_environ(environ)

            if deck.init_slide:
                for _, co in deck.init_slide.codeblocks:
                    exec(co, environ)
                print("%% executed initial setup slide.")

            if _goto:
                deck.goto(_goto)

            console.raw_input = deck.readfunc
            if readline:
                readline.parse_and_bind("tab: complete")
                readline.set_completer(rlcompleter.Completer(environ).complete)
            try:
                console.interact(deck.banner if _goto is None else "")
            except ReallyRerun as rr:
                _goto = rr.slide
            else:
                break
            finally:
                if readline:
                    # otherwise has history in the input() function used by the
                    # menu
                    readline.clear_history()

    @classmethod
    def from_path(cls, path: Path, **options: Any) -> Deck:
        """Create a Deck from slides embedded in a file at path."""

        deck = cls(path, **options)
        cls._slides_from_file(path, deck)
        return deck

    @classmethod
    def _slides_from_file(cls, path, deck):
        s_re = re.compile(r"### +slide::(.+)?$")
        f_re = re.compile(r"### +file::(.+)$")
        t_re = re.compile(r"### +title::(.+)$")
        t_re_2 = re.compile(r"^#####* (.+) #####*$")
        b_re = re.compile(r"^###( +\* .+)$")

        c_re = re.compile(r"#(?: (.*))?$")

        slide = None
        with open(path) as fh:
            lines = list(fh)
        while lines:
            line = lines.pop(0)
            m = f_re.match(line)
            if m:
                f_path = os.path.normpath(
                    os.path.join(os.path.dirname(path), m.group(1).strip())
                )
                cls._slides_from_file(f_path, deck)
                if lines and not f_re.match(lines[0]):
                    lines.pop(0)  # suppress next line
                continue

            m = t_re.match(line)
            if not m:
                m = t_re_2.match(line)
            if m:
                if slide:
                    slide.title = m.group(1).strip()
                    slide.intro = []
                    slide.lines = []
                continue

            if slide and slide.has_bullets:
                m = b_re.match(line)
                if m:
                    slide.bullets.append(m.group(1).rstrip())
                    continue

            if slide:
                m = c_re.match(line)
                if m:
                    if m.group(1):
                        slide.intro.append(m.group(1).rstrip())
                    else:
                        slide.intro.append("")
                    continue
                elif not line.isspace():
                    slide.lines = []
                elif slide.intro:
                    slide.intro.append("")

            m = s_re.match(line)
            if not m:
                if slide:
                    if not line.isspace() or slide.lines:
                        slide._append(line)
                continue

            if slide:
                slide._close()
                if getattr(slide, "init", False):
                    deck.init_slide = slide
                else:
                    deck.slides.append(slide)

            slide = cls.Slide(deck, file=fh.name, index=len(deck.slides) + 1)
            opts = m.group(1)
            if opts:
                for opt in opts:
                    if opt == "p":
                        slide.no_exec = True
                    elif opt == "x":
                        slide.never_exec = slide.no_exec = True
                    elif opt == "i":
                        slide.no_clear = True
                    elif opt == "s":
                        slide.init = True
                    elif opt == "l" and deck.short_pres:
                        slide = None
                        break
                    elif opt == "b":
                        slide.has_bullets = True

    def show_banner(self):
        print(self.banner)

    @property
    def banner(self):
        return f"""\
%%
%% Running Deck: {self.path}
%%
%% This is an interactive Python prompt.
%% Enter "?" for command list.
%% Commands always begin with a ! symbol
%% Advance slides by pressing "enter",
%% or entering the "!n" or "!next" command.
%% Quit out of this deck by entering the "!q" or "!quit" command.
"""

    def readfunc(self, prompt=""):
        if self._exec_on_return:
            prompt = "\n[press return to run code]"

        line = input(prompt)
        if self._exec_on_return or prompt == self.ps1:
            tokens = line.split()
            if self._exec_on_return or line == "":
                tokens = ("!next",)

            self._exec_on_return = False
            if (
                tokens
                and (tokens[0].startswith("!") or tokens[0] == "?")
                and tokens[0] in self._expose_map
            ):
                fn = self._expose_map[tokens[0]]
                if len(tokens) != len(inspect.getfullargspec(fn)[0]):
                    print(
                        "usage: %s %s"
                        % (
                            tokens[0],
                            " ".join(inspect.getfullargspec(fn)[0][1:]),
                        )
                    )
                else:
                    self._add_history(line)
                    fn(*tokens[1:])
                return ""
        return line

    def _decolorize(self, text):
        return re.sub(r"\!\!\{.+?}", "", text)

    def _color(self, text, color_style):
        return self._decolorize(text)

    def _highlight_text(self, text):
        return text

    @classmethod
    def _add_history(cls, line):
        if readline and line:
            readline.add_history(line)
