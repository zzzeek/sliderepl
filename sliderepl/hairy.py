from .compat import StringIO
from . import core

import sys

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name

from pygments.token import Comment
from pygments.formatters.terminal import TERMINAL_COLORS

scheme = TERMINAL_COLORS.copy()
scheme[Comment] = ('teal', 'turquoise')



_pycon_lexer = get_lexer_by_name('pycon')


class DivertableOutput(object):
    def __init__(self, fh):
        self.fh = fh
        self.divert = None

    def write(self, data):
        actor = self.divert or self.fh
        actor.write(data)

    def flush(self, *args):
        actor = self.divert or self.fh
        actor.flush(*args)

class Deck(core.Deck):
    expose = core.Deck.expose + ("highlight",)

    def __init__(self, path, **options):
        core.Deck.__init__(self, path, **options)
        self.original_stdout = sys.stdout
        self.stdout = DivertableOutput(sys.stdout)
        self._highlight = True

    def highlight(self):
        """Toggle code highlighting."""
        self._highlight = not self._highlight
        print("%% Code highlighting is now %s" % (self._highlight and "ON" or "OFF"))

    class Slide(core.Deck.Slide):
        def run(self, *args, **kwargs):
            if not self.deck._highlight:
                core.Deck.Slide.run(self, *args, **kwargs)
                return

            bg = self.deck.color == 'dark' and 'dark' or 'light'

            io = StringIO()
            stdout, stderr = self.deck.original_stdout, sys.stderr
            try:
                self.deck.stdout.divert = io
                sys.stdout = io
                sys.stderr = io
                try:
                    core.Deck.Slide.run(self, *args, **kwargs)
                    if self.deck.color in ('auto', 'light', 'dark'):
                        content = highlight(
                            io.getvalue(), _pycon_lexer, TerminalFormatter(bg=bg, colorscheme=scheme))
                    else:
                        content = io.getvalue()
                except:
                    stdout.write(io.getvalue())
                    raise
                else:
                    stdout.write(content)
            finally:
                sys.stdout = stdout
                sys.stderr = stderr
                self.deck.stdout.divert = None


