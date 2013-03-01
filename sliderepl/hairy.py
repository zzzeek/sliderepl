from .compat import StringIO
from . import core

import re
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name

from pygments.token import Comment
from pygments.formatters.terminal import TERMINAL_COLORS

scheme = TERMINAL_COLORS.copy()
scheme[Comment] = ('teal', 'turquoise')



_pycon_lexer = get_lexer_by_name('pycon')



class Deck(core.Deck):
    expose = core.Deck.expose + ("highlight",)

    def __init__(self, path, **options):
        core.Deck.__init__(self, path, **options)
        self._highlight = True

    def highlight(self):
        """Toggle code highlighting."""
        self._highlight = not self._highlight
        print("%% Code highlighting is now %s" %
                (self._highlight and "ON" or "OFF"))

    def _highlight_text(self, text):
        bg = self.color == 'dark' and 'dark' or 'light'
        if self.color in ('auto', 'light', 'dark'):
            whitespace = re.match(r'(.*?)(\s+)$', text, re.S)
            if whitespace:
                text = whitespace.group(1)
                whitespace = whitespace.group(2)
            content = highlight(
                text, _pycon_lexer,
                    TerminalFormatter(bg=bg, colorscheme=scheme))
            if whitespace:
                content = content.rstrip() + whitespace
        else:
            content = text
        return content

