#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
import itertools
import math
import re
import urllib
import urllib.parse

from .string_dates import *
from .util import *
from . import loader

config = loader.search_config


class URL:
    def __init__(self, arg, **kwargs):
        self.year = self.res = self.tags = None
        self.res_score = self.tag_score = None
        if arg:
            if isinstance(arg, str):
                self.from_text(arg)
        self.update(kwargs)
    def update(self, d):
        self.__dict__.update(d)
    def __str__(self, urlunsplit=urllib.parse.urlunsplit):
        return urlunsplit(self.urlparts)
    def get_words(self):
        """
        Tokenizes and strips out year
        """
        wc = collections.Counter(self.filepart)
        if (wc["'"] % 2) or (wc["’"] % 2):
            regex=re.compile("[^a-zA-Z0-9'’]")
        else:
            regex=re.compile("[^a-zA-Z0-9]")
        words = [ w for w in regex.split(self.filepart) if w ]
        results = []
        for w in words:
            # if several numbers are in this range, the last is picked
            if w.isdigit():
                if (1970 <= int(w) <= current_year):
                    self.year = int(w)
                else:
                    results.append(w)
            else:
                results.append(w)
        if not self.year:
            self.year, replace_regex = get_year_parser(self.filepart)
            if replace_regex:
                fp, _ = replace_regex.subn('', self.filepart)
                results = [ w for w in regex.split(fp) if w ]
        return results
    def tokenize(self, *args, \
                common_words=config.common_words, \
                resolutions=config.resolutions, \
                tag_terms=config.tag_terms):
        """
        Strips out codes for resolution and format
        """
        assert not self.res_score
        assert not self.tag_score
        words0 = self.get_words()
        self.res_score, words1 = resolutions.replace_tokens(words0, reducer=max)
        self.tag_score, non_tags = tag_terms.replace_tokens(w for w in words1 if not w.lower() in common_words)
        if non_tags and (self.title == self.filepart):
            self.title = ' '.join(non_tags)
        return non_tags
    def __lt__(self, other):
        return str(self) < str(other)
    def from_text(self, text, *args, \
                remove_remote_pagename=None, \
                urlsplit=urllib.parse.urlsplit, \
                unquote=urllib.parse.unquote):
        parts = urlsplit(text)
        if remove_remote_pagename is None:
            if parts.hostname.lower() == 'openload.co':
                remove_remote_pagename = True
        ppath, qfilename = pathsplit(parts.path)
        filepart = filename = urllib.parse.unquote(qfilename)
        ext = None
        if '.' in filename:
            filepart, ext = splitext(filename)
            if remove_remote_pagename:
                parts = parts._replace(path=ppath) # unsupported?
        self.urlparts = parts
        self.title = self.filepart = filepart
        self.filename, self.ext = filename, ext


def read_file(arg, mode='rU'):
    results = []
    if isinstance(arg, str):
        f = open(arg, mode)
    else: # assume iterable
        f = arg
    for order, line in enumerate(f, start=1):
        line = line.strip()
        # TODO: here is a good opportunity to allow in-place renaming
        if line:
            results.append( URL(line, order=order) )
    return results


def tokenize_urls(arg, counts=None):
    """
    Returns urls ordered into possible groups, based on common words,
    sorted by frequency of those words.
    """
    groupings = groupby(read_file(arg), key=lambda url: \
            [t.lower() for t in url.tokenize()] )
    c = counts or collections.Counter()
    for tokens, urls in groupings.items():
        f = len(urls)
        for t in tokens:
            c[t] += f
    if __debug__:
        debug("Most frequent words in titles:")
        for (g, word_count) in itertools.groupby(c.most_common(), \
                key=lambda row: int(math.log2(row[1])) ):
            if (g < 3): # 2**3 = 8
                break
            word_count = list(word_count)
            total = sum(c for w, c in word_count)
            words = ' '.join(sorted(w for w, c in word_count))
            debug( "%.1f-ish matches for %s", total/len(word_count), words)
    scores = { k: math.log2(v) for k, v in c.items() }
    def score_sort(tokens):
        return -sum(scores.get(t, 0) for t in tokens)
    return sorted(groupings.items(), key=lambda row: score_sort(row[0]))
def score_urls(*args, \
        replace_tokens=config.search_terms.replace_tokens, **kwargs):
    """
    Returns urls ordered by search relevance
    """
    def search_key(tokens):
        score, _ = replace_tokens(tokens)
        return -score
    for score, urls in sorted( (search_key(tokens), urls) \
            for tokens, urls in tokenize_urls(*args, **kwargs)):
        for u in urls:
            yield score, u
def sort_urls(*args, order='default', **kwargs):
    def highest_resolution(row):
        url = row[1]
        return -url.res_score
    def latest(row, current_year=current_year, default_year=current_year-3):
        url = row[1]
        return current_year-(url.year or default_year), url.order
    def highest_rank(row):
        return (row[0], *latest(row))
    def combo(row):
        year, order = latest(row)
        return (year, row[0], order)
    if callable(order):
        key = order
    else:
        key = { 'default': combo,
                None: combo,
                'highest_rank': highest_rank,
                'highest_resolution': highest_resolution,
                'latest': latest,
                'word_popularity': None }[order]
    if key:
        for _, url in sorted(score_urls(*args, **kwargs), key=key):
            yield url
    else:
        for _, urls in tokenize_urls(*args, **kwargs):
            yield from urls
