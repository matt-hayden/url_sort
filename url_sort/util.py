# Intended for 'from .util import *'

import collections
import functools
import itertools
import os, os.path
import re
import unicodedata

from datetime import datetime, timedelta, timezone
import dateutil.parser

now = datetime.now(timezone.utc).date()
current_year = now.year

@functools.lru_cache()
def regex(*args, **kwargs):
    return re.compile(*args, **kwargs)

class SumOfSquaresCounter:
    """
    Statistical parameter collector for Counter() dicts.
    Some consideration is provided for adding floating point numbers of different
    magnitude.
    """
    def __init__(self, arg=None, **kwargs):
        if arg:
            freqs = arg if isinstance(arg, collections.Counter) else collections.Counter(arg)
            n = self.n = sum(freqs.values())
            if n:
                sxf = sorted( (x**2, x, f) for x, f in freqs.items() )
                s = ss = 0
                for x2, x, f in sxf:
                    s += x*f
                    ss += x2*f
                self.s = s
                self.ss = ss
        self.__dict__.update(kwargs)
    def __add__(self, other):
        return SumOfSquaresCounter(ss=self.ss+other.ss, s=self.s+other.s, n=self.n+other.n)
    def mean_variance(self):
        if self.n:
            v = self.ss-(self.s**2)/self.n
            return self.s/n, v
        return None, None
def mean_variance(arg):
    """
    Return (mean, sample variance). Standard deviation = sqrt(sample variance)
    Pass a collections.Counter if you can.
    """
    return SumOfSquaresCounter(arg).mean_variance()
def mean(*args, **kwargs):
    m, _ = mean_variance(*args, **kwargs)
    return m

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
    One level of recursion. For more, see os.walk().
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
    return ''.join('-' if (c in dropchars) else c for c in compatible_string(text).replace(' ', '_'))


def groupby(iterable, key, factory=None):
    def tuplize(arg):
        return tuple(arg) if isinstance(arg, list) else arg
    if factory is None:
        factory = collections.OrderedDict()
    keyed = sorted((key(v), v) for v in iterable)
    for g, kiter in itertools.groupby(keyed, key=lambda row: tuplize(row[0]) ):
        factory[g] = [ v for (k, v) in kiter ]
    return factory

@functools.lru_cache(maxsize=1<<10) # Less than 1461 = 4 years
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
            'bracket': regex('(\[)([^\]]+)(\])'),
            'parens': regex('([(])([^)]+)([)])'),
            'aquote': regex("([`])([^']+)(['])"),
            }
    st = text
    for x in wrapme.values():
        st = x.sub('\0\\2\0', st)
    st = regex('[^a-zA-Z0-9,!?]{2,}').sub('\0', st)
    st = regex('([.](AVI|MKV|MP[34]|WMV))([.]|$)').sub('\0\\1\0\\2', st, re.IGNORECASE)
    if regex('[a-z]{2,}').match(st):
        st = regex('([A-Z.]{3,})([^a-zA-Z0-9])').sub('\0\\1\0\\2', st)
    return st

def media_filename_splitter(text):
    wrapme = {
            'formats':  regex('(MP[34]|[hHxX]264)', re.IGNORECASE),
            'codecs':   regex('((AAC|DD_?\d)_?(\d+([.]\d)?)?)'),
            'Ultra-HD': regex('([A-Z][a-zA-Z]+-HD)'),
            'HD-TS':    regex('(HD-[A-Z]+)'),
            }
    st = filename_splitter(text)
    for x in wrapme.values():
        st = x.sub('\0\\1\0', st)
    # 1080p, for example
    st = regex('([1-9]\d{2,}[ _]?[pP])([^a-zA-Z0-9]|$)').sub('\0\\1\0\\2', st)
    return st

def splitter(text):
    # stage 0
    st = compatible_string(text)
    if not st:
        return [text], 0
    # stage 1
    st = media_filename_splitter(st)
    # decimals and numerals of 6 or more
    st = regex('([^a-zA-Z\0]{6,})').sub('\0\\1\0', st)
    if '\0' not in st:
        return [text], 1
    # stage 2
    ts = [ _.strip('._ -') for _ in st.split('\0') ]
    # expect no \0 from here on
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
        if not regex('[a-zA-Z]').match(t):
            tt = t
            while tt and not tt[0].isdigit():
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
