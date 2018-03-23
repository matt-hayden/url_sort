#! /usr/bin/env python3
import collections
import itertools
import os, os.path
import re
import unicodedata

from datetime import datetime, timedelta, timezone
import dateutil.parser

now = datetime.now(timezone.utc).date()
current_year = now.year

def mean(iterable):
    n = s = 0
    for n, i in enumerate(iterable, start=1):
        s += i
    return s/n if n else None


def case_insensitive_replace(haystack, needle, replacement):
    splitted = re.split(needle, haystack, flags=re.IGNORECASE)
    return replacement.join(splitted)


def pathsplit(text):
    p = text.rsplit('/', 1)
    if len(p) == 1:
        return '', p[0]
    return p


def splitext(text):
    p = text.rsplit('.', 1)
    if len(p) == 1:
        return p[0], ''
    return p[0], '.'+p[-1]


def expand_dirs(*args, exts='.list'.split()):
    """
    One level of recursion
    """
    for arg in args:
        if os.path.isdir(arg):
            for fn in sorted(os.listdir(arg)):
                _, ext = os.path.splitext(fn)
                if ext.lower() in exts:
                   yield os.path.join(arg, fn)
        else:
            yield arg


def clean_filename(text, dropchars='/;:<>&'):
    return ''.join('-' if (c in dropchars) else c for c in text.replace(' ', '_'))


def groupby(iterable, key, factory=None):
    def tuplize(arg):
        if isinstance(arg, list):
            return tuple(arg)
        return arg
    if factory is None:
        factory = collections.OrderedDict()
    keyed = sorted((key(v), v) for v in iterable)
    for g, kiter in itertools.groupby(keyed, key=lambda row: tuplize(row[0]) ):
        factory[g] = [ v for (k, v) in kiter ]
    return factory

def parse_date(arg, \
        earliest=datetime(1921, 1, 1).date(), \
        latest=now+timedelta(days=2), \
        parse=dateutil.parser.parse):
    if (len(arg) == 6) and arg.isdigit():
        d = parse(arg, dayfirst=True).date()
        if (earliest < d < latest):
            return d
    t = arg.replace('_', '.')
    d = parse(t, yearfirst=True).date()
    if (earliest < d < latest):
        return d
    d = parse(t, dayfirst=True).date()
    if (earliest < d < latest):
        return d

def compatible_string(text, \
        normalize=unicodedata.normalize, \
        category=unicodedata.category):
   return ''.join(c for c in normalize('NFD', text) if category(c) != 'Mn')

def filename_splitter(text):
    wrapme = {
            'bracket': re.compile('(\[)([^\]]+)(\])'),
            'parens': re.compile('([(])([^)]+)([)])'),
            'aquote': re.compile("([`])([^']+)(['])"),
            }
    st = text
    for regex in wrapme.values():
        st = regex.sub('\257\\2\257', st)
    st = re.sub('[^a-zA-Z0-9,!?]{2,}', '\257', st)
    st = re.sub('([.](MKV|MP[34]))([.]|$)', '\257\\1\257\\2', st, re.IGNORECASE)
    if re.match('[a-z]{2,}', st):
        st = re.sub('([A-Z.]{3,})[^a-z]', '\257\\1\257\2', st)
    return st

def media_filename_splitter(text):
    wrapme = {
            'formats':  re.compile('(MP[34]|[hHxX]264)', re.IGNORECASE),
            'codecs':   re.compile('((AAC|DD_?\d)_?(\d+([.]\d)?)?)'),
            'Ultra-HD': re.compile('([A-Z][a-zA-Z]+-HD)'),
            'HD-TS':    re.compile('(HD-[A-Z]+)'),
            }
    st = filename_splitter(text)
    for regex in wrapme.values():
        st = regex.sub('\257\\1\257', st)
    # 1080p, for example
    st = re.sub('([1-9]\d{2,}[ _]?[pP])([^a-zA-Z0-9]|$)', '\257\\1\257\\2', st)
    return st

def splitter(text):
    # stage 0
    st = compatible_string(text)
    if not st:
        return [text], 0
    # stage 1
    st = media_filename_splitter(st)
    # decimals and numerals of 6 or more
    st = re.sub('([^a-zA-Z\257]{6,})', '\257\\1\257', st)
    if '\257' not in st:
        return [text], 1
    # stage 2
    ts = [ _.strip('._ -') for _ in st.split('\257') ]
    ts = [ _ for _ in ts if _ ]
    if len(ts) <= 1:
        ts = re.split("[^a-zA-Z0-9'’]+", st)
        return ts, 2
    # stage 3
    return ts, 3

def get_year_tag(filename_parts):
    """
    Modifies the list filename_parts in-place
    """
    potential_years = []
    for t in filename_parts:
        if (len(t) == 4) and t.isdigit():
            i = int(t)
            if (1920 < i <= current_year):
                potential_years.append(i)
    if 1 == len(potential_years):
        year = potential_years.pop()
        filename_parts.remove(str(year))
        return year

def get_date_tag(filename_parts):
    """
    Modifies the list filename_parts in-place
    """
    potential_dates = {}
    for t in filename_parts:
        if not isinstance(t, str):
            continue
        if not 6 <= len(t):
            continue
        if not re.match('[a-zA-Z]', t):
            tt = t
            while tt and tt[0] not in '0123456789':
                tt = tt[1:]
            try:
                d = parse_date(tt)
            except ValueError:
                d = None
            if d:
                potential_dates[t] = d
    if 1 == len(potential_dates):
        (t, d) = potential_dates.popitem()
        filename_parts.remove(t)
        return d
