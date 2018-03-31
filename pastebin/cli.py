#! /usr/bin/env python3
"""Refresh a mailbox (perhaps folder is better parlance) that only receives pastebin.com updates.

Usage:
  pastebin_mailbox_refresh [ -v | -vv ] [options] [credentials]

Options:
  -h --help         This help
  -b --by=key       Set the sort key
     --latest=N     Only read the latest N (UNSEEN) messages
  -s --dry-run      No deletey
  -v --verbose      More output, use -vv or even more

Output options:
  --list=filename   Input lines are sorted to output
  --text=filename   Unstructured #-commented lines to output
  --text-age=N      URL matches older than N hours are considered expired [default: 64]
  --m3u=filename    Playlists are concatenated, descending by time
  --m3u-age=N       M3U matches older than N hours are considered expired [default: 8]
  --onion=filename  Logs containing .onion links
"""

DEFAULT_CREDFILE='~/.config/pastebin_mailbox_refresh.json'

from datetime import datetime, timedelta
import json
import os, os.path
import sys

from docopt import docopt

import pastebin.mailbox

from url_sort.parser import *

from .persistent_cache import TextArgMemo

def main():
    import logging
    options = docopt(__doc__, version='1.0.0')
    verbose = options.pop('--verbose')
    if verbose:
        logging.basicConfig(level=logging.DEBUG if (1 < verbose) else logging.INFO)
    execname, *args = sys.argv
    try:
        cred_file = os.path.expanduser(options.pop('credentials', None) or DEFAULT_CREDFILE)
        with open(cred_file) as fi:
            creds = json.load(fi)
        safe = options.pop('--dry-run')
        order = options.pop('--by')
        latest = options.pop('--latest')
        list_filename = options.pop('--list')
        text_filename = options.pop('--text')
        text_age = { 'hours': int(options.pop('--text-age')) }
        m3u_filename = options.pop('--m3u')
        m3u_age = { 'hours': int(options.pop('--m3u-age')) }
        onion_filename = options.pop('--onion')
    except:
        print("Invalid option:", file=sys.stdout)
        raise
    if not isinstance(m3u_age, timedelta):
        m3u_age = timedelta(**m3u_age)
    nmatches, results = pastebin.mailbox.apply_filter(latest=latest, safe=safe, **creds)
    if not nmatches:
        print("Zero matches", file=sys.stdout)
        return 1
    urls = list(sort_urls(*results.contents['url list'], order=order))
    playlists = [ lines for age, lines in results.contents['m3u'] if age < m3u_age ]
    
    
    if list_filename and urls:
        assert isinstance(list_filename, str)
        lines = []
        for u in sorted(urls, key=lambda u: u.order):
            lines.append(u._text)
        with open(list_filename, 'w') as fo:
            fo.write('\n'.join(lines))
    if text_filename:
        assert isinstance(text_filename, str)
        with TextArgMemo(CACHE_DB) as memo:
            filtered = [ mr for mr in memo.after(text_age) if not isinstance(mr, Exception) ]
            if filtered:
                with open(text_filename, 'w') as fo:
                    fo.write('\n\n'.join(u.to_m3u() for u in filtered))
    if m3u_filename and playlists:
        assert isinstance(m3u_filename, str)
        with open(m3u_filename, 'w') as fo:
            for lines in playlists:
                fo.write('\n\n'.join(lines))
    if onion_filename and results:
        assert isinstance(onion_filename, str)
        with open(onion_filename, 'w') as fo:
            for lines in results.contents['onion links']:
                fo.write('\n'.join(lines))
