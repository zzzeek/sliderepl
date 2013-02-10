import sys

PY3 = sys.version_info[0] == 3

if PY3:
    import builtins
    exec_ = getattr(builtins, "exec")

    from io import StringIO

    raw_input_ = getattr(builtins, "input")

else:
    def exec_(_code_, _globs_=None, _locs_=None):
        """Execute code in a namespace."""
        if _globs_ is None:
            frame = sys._getframe(1)
            _globs_ = frame.f_globals
            if _locs_ is None:
                _locs_ = frame.f_locals
            del frame
        elif _locs_ is None:
            _locs_ = _globs_
        exec("""exec _code_ in _globs_, _locs_""")

    from StringIO import StringIO

    raw_input_ = raw_input