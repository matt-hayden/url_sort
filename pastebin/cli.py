#! /usr/bin/env python3
"""Refresh a mailbox (perhaps folder is better parlance) that only receives pastebin.com updates.

Usage:
  pastebin_mailbox_refresh [options] [credentials]

Options:
  -h --help     This help
  -b --by=key   Set the sort key
     --latest=N Only read the latest N (UNSEEN) messages
  -s --dry-run  No deletey
  -v --verbose  More output
"""

import json
import os, os.path
import sys

from docopt import docopt

import pastebin.mailbox


def main(verbose=__debug__):
    options = docopt(__doc__, version='1.0.0')
    execname, *args = sys.argv
    cred_file = os.path.expanduser(options.pop('credentials', None) or '~/.config/pastebin_mailbox_refresh.json')
    with open(cred_file) as fi:
        creds = json.load(fi)
    nmatches, result = pastebin.mailbox.apply_filter(latest=options.pop('--latest'), safe=options.pop('--dry-run'), **creds)
    if result:
        try:
            #print("%d matches and %s" %(nmatches, result))
            print(result.process_url_lists(order=options.pop('--by')))
        except BrokenPipeError:
            pass
        return 0
    else:
        return 1


if __name__ == '__main__':
    import logging
    if __debug__:
        logging.basicConfig(level=logging.DEBUG)
    sys.exit(main())
