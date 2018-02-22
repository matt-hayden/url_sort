#! /usr/bin/env python3
import collections
import itertools


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
