#! /usr/bin/env python3
import fileinput
import logging
import sys

from .parser import sort_urls


def main():
    # TODO: argument parsing
    eol = '\n' # '\x00'
    verbose = False # __debug__
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    score_url = list( sort_urls(fileinput.input()) ) # arrives sorted by logical name
    if True:
        score_url.sort()
    try:
        print( eol.join(str(u) for score, u in score_url) )
    except BrokenPipeError:
        sys.exit(0)
    except:
        raise
