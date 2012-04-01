# sliderepl
#   Copyright (c) Jason Kirtland <jek@discorporate.us>
#   sliderepl is released under the MIT License:
#   http://www.opensource.org/licenses/mit-license.php
#   Modified by Jason Kirtland and Mike Bayer for PyCon 2009

environ = globals().copy()
import code, inspect, itertools, os, re, sys, traceback
from datetime import datetime
try:
    import rlcompleter, readline
except ImportError:
    readline = None

if sys.platform == 'win32':
    clearcmd = "cls"
else:
    clearcmd = "clear"

class Deck(object):
    expose = ('next', 'goto', 'show', 'info', 'prev','quick',
              'rerun', 'xecute', 'presentation', 'timer')

    def __init__(self, path=None, **options):
        self.path = path or '<no file>'
        self.slides = []
        self.current = 0
        self.color = options.get('color', None)
        self._set_presentation(options.get('presentation', False))
        self._set_quick(options.get('quick', True))
        self._set_show_timer(options.get('timer', False))
        self.pending_exec = False
        self._letter_commands = {}
        self._expose_map = dict((name, getattr(self, name))
                                for name in self.expose)

        for name in self.expose:
            c = name[0]
            if c in self._expose_map:
                c = name[0:2]
            self._expose_map[c] = getattr(self, name)
            self._letter_commands[name] = c
        self._expose_map['?'] = self.commands

    def start(self):
        pass

    def _set_show_timer(self, mode):
        self._show_timer = mode
        print "%% show timer is now %s" % (self._show_timer and "ON" or "OFF")

    def _set_presentation(self, mode):
        self._presentation = mode
        print "%% presentation mode is now %s" % (self._presentation and "ON" or "OFF")

    def presentation(self):
        """Toggle presentation mode"""
        self._set_presentation(not self._presentation)

    def quick(self):
         """quick on|off, type enter to advance to the next slide."""

         self._set_quick(not self._quick)

    def timer(self):
        """Show current time in slide header"""

        self._set_show_timer(not self._show_timer)

    def _set_quick(self, mode):
        self._quick = mode
        print "%% quick mode (enter advances) is now %s"  % (self._quick and "ON" or "OFF")

    def xecute(self):
        """Execute the code for the current slide."""

        self._do_slide(self.current, run=True, echo=False)
        self.pending_exec = False

    def rerun(self):
        """Re-run the current slide."""

        self.pending_exec = False
        self._do_slide(self.current)

    def prev(self):
        """Advance to the previous slide."""

        self.pending_exec = False
        self.current -= 1

        self._do_slide(self.current)

    def next(self):
        """Advance to the next slide."""
        self._next()

    def _next(self, run=True):
        """Advance to the next slide."""

        if self.pending_exec:
            self.xecute()
            return

        if self.current >= len(self.slides):
            print "% The slideshow is over."
            return
        self.current += 1

        self._do_slide(self.current, run=run)

    def _do_slide(self, num, run=True, echo=True):
        slide = self.slides[num - 1]
        if self._show_timer:
            timer = " " + datetime.now().strftime("%H:%M:%S")
        else:
            timer = ""
        if echo:
            if self._presentation:
                if not getattr(slide, 'no_clear', False):
                    os.system(clearcmd)
                    print slide._banner(timer)
                else:
                    print ""
            else:
                print slide._banner(timer)

        slide.run(run=run, echo=echo)
        if run != 'force' and getattr(slide, 'no_exec', False):
            self.pending_exec = True

    def slide_actor(fn):
        def decorated(self, slide_number):
            if isinstance(slide_number, str) and not slide_number.isdigit():
                print "%% Usage: %s slide_number" % fn.__name__
                return
            num = int(slide_number)
            if num < 1 or num > len(self.slides):
                print "%% Slide #%s is out of range (1 - %s)." % (
                    num, len(self.slides))
            else:
                return fn(self, num)
        decorated.__doc__ = fn.__doc__
        return decorated

    @slide_actor
    def show(self, slide_number):
        """show NUM, display a slide without executing it."""

        self._do_slide(slide_number, False)

    @slide_actor
    def goto(self, slide_number):
        """goto NUM, skip forward to another slide or go back to a previous slide."""

        self.pending_exec = False
        if slide_number <= self.current:
            self.current = slide_number
            self._do_slide(self.current, run='force')
        else:
            for _ in range(slide_number - self.current):
                self._next(run='force')

    def info(self):
        """Display information about this slide deck."""
        print "%% Now at slide %s of %s from deck %s" % (
            self.current, len(self.slides), self.path)

    def commands(self):
        """Display this help message."""
        for cmd in ('?',) + self.expose:
            print "% " + cmd + \
                (cmd in self._letter_commands and " / " + self._letter_commands[cmd] or "")
            print "%\t" + self._expose_map[cmd].__doc__

    del slide_actor

    class Slide(object):
        def __init__(self, deck, file, index):
            self.deck = deck
            self.codeblocks = []
            self.lines = []
            self.intro = []
            self._stack = []
            self._level = None
            self.file = file
            self.index = index
            self.title = None

        def _banner(self, timer):
            banner = ""

            box_size = 63

            header = "%s / %d" % (self.file, self.index)
            if timer:
                header += " / " + timer

            if header:
                box_size = max(box_size, len(header))

            title = None

            if self.title:
                title = "%%% " + self.title

                box_size = max(box_size, len(title))
            if self.intro:
                box_size = max(*[box_size] + [len(l) for l in self.intro])

            box_size += 4

            if not self.deck._presentation:
                banner += "\n"

            banner += "+%s+\n" % ("-" * (box_size - 1))

            if title or self.intro:

                if title:
                    banner += "| %s%s|\n" % (title, (" " * (box_size - len(title) - 2)))

                if self.intro:
                    banner += "\n".join(
                                        "| %s%s|" % (l, (" " * (box_size - len(l) - 2)))
                                        for l in self.intro) + "\n"

            banner += "|%s%s |\n" % (" " * (box_size - len(header) - 2), header)

            banner += "+%s+\n" % ("-" * (box_size - 1))

            return banner

        def run(self, run=True, echo=True):
            if run is True and \
                echo and getattr(self, 'no_exec', False):
                run = False

            for i, (display, co) in enumerate(self.codeblocks):
                if echo and not getattr(self, 'no_echo', False):
                    shown = [getattr(sys, 'ps1', '>>> ') + display[0]]

                    space = False
                    for l in display[1:]:
                        if l.startswith(' '):
                            shown.append(getattr(sys, 'ps2', '... ') + l)
                        elif not l.isspace():
                            shown.append(getattr(sys, 'ps1', '>>> ') + l)
                        else:
                            shown.append(l)

                    #shown.extend([getattr(sys, 'ps2', '... ') + l
                    #                      for l in display[1:] if not ])


                    Deck._add_history(''.join(display).rstrip())
                    shown = ''.join(shown).rstrip()

                    print shown

                    if len(display) > 1:
                        if not re.match(r'#[\s\n]', display[0]) or \
                            (i + 1< len(self.codeblocks) and 
                                not re.match(r'#[\s\n]', self.codeblocks[i+1][0][0])):
                            print ""

                if run:
                    try:
                        exec co in environ
                    except:
                        traceback.print_exc()
            if not run:
                print "%%% next to execute"
                #print getattr(sys, 'ps1', '>>> ') + ("# next to execute")

        def __str__(self):
            return ''.join(self.lines)

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

        def _compile(self):
            style = getattr(self, 'no_return', False) and 'exec' or 'single'
            try:
                return code.compile_command(''.join(self._stack), '<input>', style)
            except:
                print "code:", ''.join(self._stack)
                raise

        def _pop(self):
            self._stack.reverse()
            lines = list(self._stack) #itertools.dropwhile(str.isspace, self._stack))
            lines.reverse()
            self._stack = []
            return lines

    @classmethod
    def run(cls, path=None, **options):
        """Run an interactive session for a Deck and exit when complete."""
        if path is None:
            path = sys.argv[0]
        deck = cls.from_path(path, **options)
        if not deck:
            sys.stderr.write("Aborting: no slides!\n")
            sys.exit(-1)

        deck.start()

        if options.get('run_all'):
            deck.goto(len(deck.slides))
            sys.exit(0)

        console = code.InteractiveConsole()
        global environ
        environ = console.locals
        console.raw_input = deck.readfunc
        if readline:
            readline.parse_and_bind('tab: complete')
            readline.set_completer(rlcompleter.Completer(environ).complete)
        console.interact(deck.banner)
        sys.exit(0)

    @classmethod
    def from_path(cls, path, **options):
        """Create a Deck from slides embedded in a file at path."""

        deck = cls(path, **options)
        cls._slides_from_file(path, deck)
        return deck.slides and deck or None

    @classmethod
    def _slides_from_file(cls, path, deck):
        s_re = re.compile(r'### +slide::(?:\s*(\d+|end))?'
                          r'(?:\s+-\*-\s*(.*?)-\*-)?')
        f_re = re.compile(r'### +file::(.+)$')
        t_re = re.compile(r'### +title::(.+)$')
        t_re_2 = re.compile(r'^#####* (.+) #####*$')

        e_re = re.compile(r'### +encoded::')
        c_re = re.compile(r'#($| .*$)')
        a_re = re.compile(r',\s*')

        slide  = None
        with open(path) as fh:
            lines = list(fh)
        while lines:
            line = lines.pop(0)
            m = f_re.match(line)
            if m:
                f_path = os.path.normpath(
                            os.path.join(
                                os.path.dirname(path), 
                                m.group(1).strip()))
                cls._slides_from_file(f_path, deck)
                if lines and not f_re.match(lines[0]):
                    lines.pop(0) # suppress next line
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

            if slide and not has_body:
                m = c_re.match(line)
                if m:
                    slide.intro.append(m.group(1).strip())
                    continue
                elif not line.isspace():
                    has_body = True
                    slide.lines = []
                elif slide.intro:
                    slide.intro.append("")

            m = e_re.match(line)
            if m:
                encoded = ""
                while lines:
                    line = lines.pop(0)
                    if not line.startswith("###"):
                        break
                    else:
                        encoded += line[4:]
                for line in encoded.decode("base64").decode("zlib").split("\n"):
                    slide._append(line + "\n")

            m = s_re.match(line)
            if not m:
                if slide:
                    if not line.isspace() or slide.lines:
                        slide._append(line)
                continue

            if slide:
                slide._close()
                deck.slides.append(slide)

            number, opts = m.groups()
            if number == 'end':
                break
            slide = cls.Slide(deck, file=fh.name, index=len(deck.slides) + 1)
            has_body = False
            for option in opts and a_re.split(opts) or []:
                setattr(slide, option.strip(), True)

    def show_banner(self):
        print self.banner

    @property
    def banner(self):

        return """\
%% 
%% Slide Runner
%%
%% This is an interactive Python prompt.
%% Enter "?" for help.
%% Advance slides by pressing "enter" (quick mode), 
%% or entering the "n" or "next" command."""

    def readfunc(self, prompt=''):
        line = raw_input(prompt)
        if prompt == getattr(sys, 'ps1', '>>> '):
            tokens = line.split()
            if line == '' and self._quick:
                tokens = ('next',)

            if tokens and tokens[0] in self._expose_map:
                fn = self._expose_map[tokens[0]]
                if len(tokens) != len(inspect.getargspec(fn)[0]):
                    print "usage: %s %s" % (
                        tokens[0], ' '.join(inspect.getargspec(fn)[0][1:]))
                else:
                    self._add_history(line)
                    fn(*tokens[1:])
                return ''
        return line

    @classmethod
    def _add_history(cls, line):
        if readline and line:
            readline.add_history(line)
