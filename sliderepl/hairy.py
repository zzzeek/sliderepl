from .compat import StringIO
from . import core

import re
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name

from pygments.token import Comment
from pygments.formatters.terminal import TERMINAL_COLORS
import sys


scheme = TERMINAL_COLORS.copy()
scheme[Comment] = ('teal', 'turquoise')



_pycon_lexer = get_lexer_by_name('pycon')


class HighlightOutput(object):
    def __init__(self, deck, lexer):
        self.deck = deck
        self.lexer = lexer

    def write(self, text):
        sys.stdout.write(self.deck._highlight_text(text, self.lexer))

    def __getattr__(self, key):
        return getattr(sys.stdout, key)

class Deck(core.Deck):
    expose = core.Deck.expose + ("highlight",)

    def __init__(self, path, **options):
        core.Deck.__init__(self, path, **options)
        self._highlight = True

    def highlight_stdout(self, lexer):
        lexer = get_lexer_by_name(lexer)
        return HighlightOutput(self, lexer)

    def highlight(self):
        """Toggle code highlighting."""
        self._highlight = not self._highlight
        print("%% Code highlighting is now %s" %
                (self._highlight and "ON" or "OFF"))

    def _highlight_text(self, text, lexer=_pycon_lexer):
        bg = self.color == 'dark' and 'dark' or 'light'
        if self._highlight and \
                self.color in ('auto', 'light', 'dark'):
            whitespace = re.match(r'(.*?)(\s+)$', text, re.S)
            if whitespace:
                text = whitespace.group(1)
                whitespace = whitespace.group(2)
            if text.strip():
                content = highlight(
                    text, lexer,
                        TerminalFormatter(bg=bg, colorscheme=scheme)).rstrip()
            else:
                content = text
            if whitespace:
                content = content + whitespace
        else:
            content = text
        return content

