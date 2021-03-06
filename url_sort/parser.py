#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
import itertools
import math
import urllib.parse
import sys

if sys.stderr.isatty():
    from tqdm import tqdm as progress
else:
    def progress(arg, **kwargs):
        return arg


from . import loader
from .persistent_cache import TextArgMemo
from .url import URL
from .util import *

config = loader.search_config


CACHE_DB = '~/.cache/urlsort.db'


class OpenloadURL(URL):
    def from_text(self, *args, **kwargs):
        super().from_text(*args, **kwargs)
        ppath, _ = pathsplit(self.urlparts.path)
        self.urlparts = self.urlparts._replace(path=ppath)


def _read_files(*args, mode='rU'):
    order=0
    with TextArgMemo(CACHE_DB) as memo:
        @memo.wrap
        def urlsort_url(line):
            if 'openload.co' in line.lower():
                return OpenloadURL(line)
            else:
                return URL(line)
        for arg in args:
            if isinstance(arg, str):
                f = open(arg, mode)
            else: # assume iterable
                f = arg
            for order, line in enumerate(f, start=order+1):
                line = line.strip()
                if line:
                    u = urlsort_url(line)
                    ### memo-wrapped functions can return a stealthy zombie exception from previous runs.
                    if isinstance(u, Exception):
                        raise u
                    ###
                    u.order = order
                    yield u
def read_files(*args, **kwargs):
    return list(_read_files(*args, **kwargs))


def tokenize_urls(*args, counts=None, common_words=config.common_words):
    """
    Returns urls ordered into possible groups, based on common words,
    sorted by frequency of those words.
    """
    def key(url):
        words = url.tokenize()
        return [ t.lower() for t in words ]
    groupings = groupby(progress(read_files(*args), unit='lines', desc="Reading %d files" % len(args)), key=key)
    c = counts or collections.Counter()
    for tokens, urls in groupings.items():
        f = len(urls)
        for t in tokens:
            if not t.isdigit() and not (t.lower() in common_words):
                c[t] += f
    scores = { k: math.log2(v) for k, v in c.items() }
    def score_sort(row):
        tokens, urls = row
        return -sum(scores.get(t, 0) for t in tokens)
    return sorted(groupings.items(), key=score_sort)
def score_urls(*args, \
        search_terms=config.search_terms, **kwargs):
    """
    Returns urls ordered by search relevance
    """
    def search_key(tokens, default=0):
        score, _, _ = search_terms.replace_terms(tokens)
        return -(score or default)
    tags = collections.Counter()
    score_by_tags = collections.Counter()
    ntitles = nadult = 0
    # score is negative
    i = progress(tokenize_urls(*args, **kwargs), unit='lines', desc='parsing') 
    for score, urls in sorted( (search_key(tokens), urls) \
            for tokens, urls in i ):
        ntitles += 1
        nadult += int(any(hasattr(u, 'adult') and u.adult for u in urls))
        for u in urls:
            yield score, u
            tags['/'.join(u.tags)] += 1
            score_by_tags['/'.join(u.tags)] -= score
    if ntitles:
        nuntagged = tags.pop('')
        if nuntagged:
            info("metadata: untagged: {} ({:.0%}) avg score={:+.2f}".format( \
                    nuntagged, nuntagged/ntitles, score_by_tags['']/nuntagged))
        else:
            info("metadata:")
        info("{}/{} ({:.0%}) adult material".format(nadult, ntitles, nadult/ntitles))
        if tags:
            fieldw = max(len(t) for t in tags)
            for k, f in tags.most_common(64):
                info("\t%s %03d\tavg score=%+.2f", \
                        k.ljust(min(fieldw, 64)), f, score_by_tags[k]/f)


# Sort keys:
def highest_resolution(row):
    _, url = row
    return -(url.res_score or 0)
def latest(row, now=now, default_age=timedelta(days=2*365.25)):
    """
    age_metric is log scaled.
    """
    search_score, url = row
    age = now-url.date if url.date else default_age
    if age.days < 5:
        age_metric = -1
    else:
        age_metric = math.log(age.days)
    return age_metric, url.order
def highest_rank(row):
    search_score, url = row
    age_metric, order = latest(row)
    return (search_score, age_metric, order)
def combo(row):
    search_score, url = row
    age_metric, order = latest(row)
    # NOTE: search_score is opposite-signed for sorting reasons.
    debug("res=%.1f, tag=%.1f, search=%.1f for '%s'", \
          url.res_score, url.tag_score, -search_score, url._text)
    # Display weights:
    overall_score = (url.tag_score or 0) + 4*(url.res_score or 0) - search_score/3.14
    # NOTE: overall_score is opposite-signed for sorting reasons
    return (-overall_score, age_metric, order)
sort_keys = { 'default': combo,
    None: combo,
    'highest_rank': highest_rank,
    'highest_resolution': highest_resolution,
    'latest': latest,
    'word_popularity': None }
def sort_urls(*args, order='default', **kwargs):
    if callable(order):
        key = order
    elif order in sort_keys:
        key = sort_keys[order]
    else:
        raise ValueError("order=%s not recognized" %(order))
    if key:
        for _, url in sorted(score_urls(*args, **kwargs), key=key):
            yield url
    else:
        for _, urls in tokenize_urls(*args, **kwargs):
            yield from urls
    if __debug__:
        debug("parse_date() cache_info: %s", parse_date.cache_info())
        debug("regex() cache_info: %s", regex.cache_info())
