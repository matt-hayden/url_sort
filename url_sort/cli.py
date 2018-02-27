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
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
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
    resolution_freq, tag_freq = collections.Counter(), collections.Counter()
    try:
        for u in urls:
            print('')
            print("#", u.title, ('(%d)' % u.year) if u.year else '')
            if u.resolutions:
                resolution_freq.update(r.upper() for r in u.resolutions)
            if u.tags:
#                u.tags.sort()
#                print('# Tags:', ', '.join(t.replace('\0', '\u00A4') for t in u.tags))
                tag_freq.update(t.capitalize() for t in u.tags)
            print("# %s" % shlex.quote(u.filename))
            print(str(u))
#        info('Resolutions:')
#        for t, f in resolution_freq.most_common():
#            info(t.replace('\0', '\u00A4'))
#        info('Tags:')
#        for t, f in tag_freq.most_common():
#            info(t.replace('\0', '\u00A4'))
    except BrokenPipeError:
        sys.exit(0)
    except:
        raise
