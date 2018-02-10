#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
import itertools
import re
import urllib
import urllib.parse


from .load import common_words, resolutions, search_terms, tag_terms
info("{} common words".format(len(common_words)) )
info("resolutions: {}".format(resolutions) )
info("search_terms: {}".format(search_terms) )
info("tag_terms: {}".format(tag_terms) )


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


def read_file(filename):
    results = []
    for order, line in enumerate(open(filename, 'rU'), start=1):
        # TODO: allow in-place renaming
        results.append( from_url(line.strip(), order=order) )
    return results


def sort_urls(filename, counts=None, mincount=2):
    def sort_key(row):
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
        #debug( "{} -> {}".format(u, ' '.join(ts)) )
    urls_tokens.sort(key=sort_key)
    for g, uts in itertools.groupby(urls_tokens, key=sort_key):
        score, _ = search_terms.replace_tokens(g)
        uts = sorted(uts, key=lambda row: (-row[0].res_score, -row[0].tag_score) )
        n = len(uts)
        for u, t in uts:
            yield score, g, u
