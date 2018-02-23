#! /usr/bin/env python3
"""URL sorter.

Q: Got a list of unsorted URLs?
A: We are DEVO!

Usage:
  urlsort [options] [--] [FILE ...]

Options:
  -h --help     This help
  -b --by=key   Set the sort key
  -v --verbose  More output
"""
import logging
import shlex
import sys

from docopt import docopt

from .parser import *


def main(*FILE, verbose=__debug__):
    options = docopt(__doc__, version='1.0.0')
    FILE = FILE or options.pop('FILE') or [sys.stdin]
    verbose = verbose or options.pop('--verbose')
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    urls = sort_urls(*FILE, order=options.pop('--by'))
    try:
        for u in urls:
            print('')
            print("# %s" % u.title+(' (%d)' % u.year if u.year else ''))
            print("# %s" % shlex.quote(u.filename))
            print(str(u))
    except BrokenPipeError:
        sys.exit(0)
    except:
        raise
