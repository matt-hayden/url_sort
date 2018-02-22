#! /usr/bin/env python3
import fileinput
import logging
import sys

from .parser import *


def main(verbose=__debug__, **options):
    # TODO: argument parsing
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    urls = sort_urls(fileinput.input())
    try:
        for u in urls:
            print('')
            print('# %s' % u.filename)
            if u.year:
                print('### year: %s' % u.year)
            if u.tags:
                print('### identified by: %s' % ', '.join(u.tags))
            print(str(u))
    except BrokenPipeError:
        sys.exit(0)
    except:
        raise
