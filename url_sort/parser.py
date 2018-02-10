#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
import importlib
import itertools
import os.path
import re
import sys
import urllib
import urllib.parse


sys.path.insert(0, os.path.abspath('.'))
config_mod_name = 'load'
search_config	= importlib.import_module(config_mod_name, '.')
debug(          "Loaded search config from '%s'", str(search_config))
common_words	= search_config.common_words
info(		"{} common words".format(len(common_words)) )
resolutions	= search_config.resolutions
info(		"resolutions: {}".format(resolutions) )
search_terms	= search_config.search_terms
info(		"search_terms: {}".format(search_terms) )
tag_terms	= search_config.tag_terms
info(		"tag_terms: {}".format(tag_terms) )


def get_year(text, regex=re.compile('[^0-9](?P<year>(19|20)\d\d)')):
    m = regex.search(text)
    if m:
        return int(m.group('year'))
    Y = M = D = None
    m = re.search('[^\d](\d\d)([._])(\d\d)\\2(\d\d)', text)
    if m:
        Y = int(m.group(1))
        D = int(m.group(4))
    else:
        m = re.search('[^\d](\d\d)(\d\d)(\d\d)', text)
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


class url:
    def __init__(self, **kwargs):
        self.year = self.res = self.tags = None
        self.pop_score = self.res_score = self.tag_score = 0
        self.__dict__.update(kwargs)
    def update(self, d):
        self.__dict__.update(d)
    def __str__(self):
        return urllib.parse.urlunparse(self.parsed)
    def get_words(self, regex=re.compile('[^a-zA-Z0-9]')):
        words = [ w for w in regex.split(self.filepart) if w ]
        results = []
        for w in words:
            if w.isdigit():
                if (1970 <= int(w) <= 2018):
                    self.year = int(w)
            else:
                results.append(w)
        if not self.year:
            self.year = get_year(self.filepart)
        return results
    def tokenize(self):
        assert self.res_score == 0
        assert self.tag_score == 0
        words0 = self.get_words()
        self.res_score, words1 = resolutions.replace_tokens(words0, reducer=max)
        self.tag_score, non_tags = tag_terms.replace_tokens(w for w in words1 if not w.lower() in common_words)
        return non_tags
    def __lt__(self, other):
        return str(self) < str(other)


def from_url(text, **kwargs):
    parsed = urllib.parse.urlparse(text)
    _, qfilename = parsed.path.rsplit('/', 1)
    filepart = filename = urllib.parse.unquote(qfilename)
    ext = None
    if '.' in filename:
        filepart, ext = filename.rsplit('.', 1)
        ext = '.'+ext
    u = url(parsed=parsed, quoted_filename=qfilename, filename=filename, filepart=filepart, ext=ext)
    u.__dict__.update(kwargs)
    return u


def score_sort(url):
    """
    sort key for url objects
    """
    return -url.res_score, -url.tag_score


def read_file(arg, mode='rU'):
    results = []
    if isinstance(arg, str):
        f = open(arg, mode)
    else:
        f = arg
    for order, line in enumerate(f, start=1):
        # TODO: allow in-place renaming
        results.append( from_url(line.strip(), order=order) )
    return results


def sort_urls(filename, counts=None, mincount=2):
    """
    Returns urls ordered into possible groups, based on common words
    """
    def token_sort(row):
        _, tokens = row
        return [ t.lower() for t in tokens ]
    urls = read_file(filename)
    urls_tokens = [ (u, u.tokenize()) for u in urls ]

    c = counts or collections.Counter()
    for _, ts in urls_tokens:
        c.update(t.lower() for t in ts)
    most_common_word, max_freq = c.most_common(1).pop()
    max_freq = max_freq/3.14159
    info("Normalizing by %f", max_freq)
    if __debug__:
        debug("Most frequent words in titles:")
        for (g, word_count) in itertools.groupby(c.most_common(len(c)*3//4), key=lambda row: row[1]):
            word_count = list(word_count)
            debug( "%d matches for %s", g, ' '.join(sorted(w for w, c in word_count)) )
    scores = { k:v/max_freq for k,v in c.items() if (mincount <= v) }
    for u, ts in urls_tokens:
        assert u.pop_score == 0
        for tc in ts:
            t = tc.lower()
            if t in scores:
                u.pop_score += scores[t]
    urls_tokens.sort(key=token_sort)
    for g, uts in itertools.groupby(urls_tokens, key=token_sort):
        score, _ = search_terms.replace_tokens(g)
        uts = sorted(uts, key=lambda row: score_sort(row[0])) # arrives as generator
        #n = len(uts)
        for u, _ in uts:
            yield -score, u
