from argparse import ArgumentParser

import sys

if sys.platform=='win32':
    color_default= 'never'
else:
    color_default = 'auto'

usage = "usage: %prog [options] [filename]"
parser = OptionParser(usage=usage)

parser.add_option("--run-all", action="store_true",
                  help="Execute all slides without prompting and exit.")
parser.add_option("--presentation", action="store_true",
                  help="Presentation mode")
parser.add_option("--timer", action="store_true",
                help="Show timer")
parser.add_option("-q", "--quick", action="store_true",
                  help="'Enter' key is a shortcut for 'next'")
parser.add_option("--color", dest="color",
                  choices=('never', 'auto', 'light', 'dark'),
                  help=("Control the use of color syntax highlighting. "
                        "Choices are 'never', 'auto', 'light' and 'dark'."))

parser.set_defaults(run_all=False,
                    presentation=False,
                    quick=True,
                    color=color_default)

parse_args = parser.parse_args
