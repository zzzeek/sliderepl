import sys


if sys.stdout.isatty():
    try:
        from sliderepl.hairy import Deck
    except ImportError:
        from sliderepl.core import Deck
else:
    from sliderepl.core import Deck  # noqa
