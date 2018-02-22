#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
from datetime import datetime
import itertools
import math
import re
import urllib
import urllib.parse

from .util import *
from . import loader

current_year = datetime.now().year

config = loader.search_config


def get_year(text, *args, \
    YYYYMM      = re.compile('[^0-9](?P<year>(19|20)\d\d)'), \
    XX_MM_XX    = re.compile('[^\d](\d\d)([._])(\d\d)\\2(\d\d)'), \
    XXMMXX      = re.compile('[^\d](\d\d)(\d\d)(\d\d)') ):
    m = YYYYMM.search(text) # only first occurrance is tested
    if m:
        y = int(m.group('year'))
        if (1920 < y < current_year):
            return y
    Y = M = D = None
    m = XX_MM_XX.search(text)
    if m:
        Y = int(m.group(1))
        # Months is 3
        D = int(m.group(4))
    else:
        m = XXMMXX.search(text)
        if m:
            Y = int(m.group(1))
            D = int(m.group(3))
    if Y or D:
        if (70 <= Y <= 99):
            return 1900+Y
        if (0 <= Y <= 18):
            return 2000+Y
        Y, D = D, Y
        if (70 <= Y <= 99):
            return 1900+Y
        if (0 <= Y <= 18):
            return 2000+Y


class URL:
    def __init__(self, arg, **kwargs):
        self.year = self.res = self.tags = None
        self.pop_score = self.res_score = self.tag_score = 0
        if arg:
            if isinstance(arg, str):
                self.from_text(arg)
        self.update(kwargs)
    def update(self, d):
        self.__dict__.update(d)
    def __str__(self, urlunsplit=urllib.parse.urlunsplit):
        return urlunsplit(self.urlparts)
    def get_words(self, regex=re.compile('[^a-zA-Z0-9]')):
        """
        Tokenizes and strips out year
        """
        words = [ w for w in regex.split(self.filepart) if w ]
        results = []
        for w in words:
            # if several numbers are in this range, the last is picked
            if w.isdigit():
                if (1970 <= int(w) <= current_year):
                    self.year = int(w)
            else:
                results.append(w)
        if not self.year:
            self.year = get_year(self.filepart)
        return results
    def tokenize(self, *args, \
                common_words=config.common_words, \
                resolutions=config.resolutions, \
                tag_terms=config.tag_terms):
        """
        Strips out codes for resolution and format
        """
        assert self.res_score == 0
        assert self.tag_score == 0
        words0 = self.get_words()
        self.res_score, words1 = resolutions.replace_tokens(words0, reducer=max)
        self.tag_score, non_tags = tag_terms.replace_tokens(w for w in words1 if not w.lower() in common_words)
        return non_tags
    def __lt__(self, other):
        return str(self) < str(other)
    def from_text(self, text, *args, \
                remove_remote_pagename=None, \
                urlsplit=urllib.parse.urlsplit, \
                unquote=urllib.parse.unquote):
        parts = self.urlparts = urlsplit(text)
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
        self.filename, self.filepart, self.ext = filename, filepart, ext


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
    Returns urls ordered into possible groups, based on common words
    """
    groupings = groupby(read_file(arg), key=lambda url: [t.lower() for t in url.tokenize()] )
    c = counts or collections.Counter()
    for tokens, urls in groupings.items():
        f = len(urls)
        for t in tokens:
            c[t] += f
    if __debug__:
        debug("Most frequent words in titles:")
        for (g, word_count) in itertools.groupby(c.most_common(), key=lambda row: int(math.log2(row[1])) ):
            if (g < 3):
                break
            word_count = list(word_count)
            total = sum(c for w, c in word_count)
            words = ' '.join(sorted(w for w, c in word_count))
            debug( "%.1f-ish matches for %s", total/len(word_count), words)
    scores = { k: math.log2(v) for k, v in c.items() }
    def score_sort(tokens):
        return -sum(scores.get(t, 0) for t in tokens)
    yield from sorted(groupings.items(), key=lambda row: score_sort(row[0]))
def score_urls(arg, replace_tokens=config.search_terms.replace_tokens, **kwargs):
    """
    Returns urls ordered by search relevance
    """
    def search_key(tokens):
        score, _ = replace_tokens(tokens)
        return -score
    for score, urls in sorted( (search_key(tokens), urls) for tokens, urls in tokenize_urls(arg, **kwargs)):
        for u in urls:
            yield score, u
def sort_urls(*args, order=None, **kwargs):
    def latest(row, current_year=current_year, default_year=current_year-3):
        url = row[1]
        return current_year-(url.year or default_year), url.order
    def highest_rank(row):
        return (row[0], *latest(row))
    def combo(row):
        year, order = latest(row)
        return (year, row[0], order)
    key = { None: combo, 'highest_rank': highest_rank, 'latest': latest }[order]
    scored_urls = sorted(score_urls(*args, **kwargs), key=key)
    return [ u for s, u in scored_urls ]
