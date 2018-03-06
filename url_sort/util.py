#! /usr/bin/env python3
import collections
import itertools
import os, os.path
import re


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
