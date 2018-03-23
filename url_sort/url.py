#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

from datetime import datetime, timedelta
import re
import shlex
import urllib.parse

from .util import *
from . import loader

config = loader.search_config


class URLBase:
    def __init__(self, arg, order=None, **kwargs):
        self.resolutions, self.tags = [], []
        self.date = None
        self.res_score = self.tag_score = None
        if order is not None:
            self.order = order
        if arg:
            if isinstance(arg, str):
                self._text = arg
                self.from_text(arg, **kwargs)
    def update(self, d):
        self.__dict__.update(d)
    def __str__(self, urlunsplit=urllib.parse.urlunsplit):
        return urlunsplit(self.urlparts)
    def __hash__(self):
        return hash(self.urlparts[1:3])
    def __lt__(self, other):
        return str(self) < str(other)
class URL(URLBase):
    _rippers = 'AMIABLE CPG CTG DIAMOND DRONES EVO GECKOS KLEENEX KTR PLAYNOW RARBG ROVER SEXXX SPARKS VBT VSEX XVID'.split()
    def get_words(self):
        return [ str(_) for _ in self.get_word_groups() ]
    def get_word_groups(self):
        """
        Tokenizes and strips out dates
        """
        splitted, split_stage = splitter(self.filepart)
        if not self.date:
            d = get_date_tag(splitted)
            if d:
                self.date = d
        if not self.date:
            y = get_year_tag(splitted)
            if y:
                self.date = datetime(y, 1, 1).date()
        #debug("%s -> %s", self.filepart, splitted)
        #return [ str(_) for _ in splitted ]
        return splitted
    def tokenize(self, \
                common_words=config.common_words, \
                resolutions=config.resolutions, \
                tag_terms=config.tag_terms):
        """
        Strips out codes for resolution and format
        """
        assert not self.res_score
        assert not self.tag_score
        word_groups = []
        res_score = tag_score = None
        for wg in self.get_word_groups():
            words = re.split('[^a-zA-Z0-9,!?]+', wg)
            for w in words:
                if w.upper() == 'XXX': # don't want this in logs
                    self.adult = 'XXX'
            if hasattr(self, 'adult') and self.adult:
                words = [ w for w in words if w.upper() != 'XXX' ]
            x, rs, words = resolutions.replace_terms(words, reducer=max)
            if x:
                res_score = x if (res_score is None) else max(x, res_score)
            self.resolutions.extend(rs)
            x, ts, words = tag_terms.replace_terms(words)
            if x:
                if (tag_score is None):
                    tag_score = x
                else:
                    tag_score += x
            self.tags.extend(ts)
            word_groups.extend(w for w in words if w)
        if not word_groups:
            return []
        last_word = word_groups[-1]
        if last_word[-1].isupper():
            last_word = last_word.upper()
        if last_word.upper() in self._rippers:
            self.ripper = word_groups.pop(-1)
        self.res_score = res_score or 0
        self.tag_score = tag_score or 0
        if (self.title == self.filepart):
            new_title = ' '.join(word_groups)
            if new_title in (new_title.upper(), new_title.lower()):
                new_title = ' '.join(w.capitalize() for w in word_groups)
            self.title = new_title
        return word_groups
    def from_text(self, text, *args, \
                remove_remote_pagename=None, \
                urlsplit=urllib.parse.urlsplit, \
                unquote=urllib.parse.unquote):
        parts = urlsplit(text)
        ppath, qfilename = pathsplit(parts.path)
        filepart = filename = urllib.parse.unquote(qfilename)
        ext = None
        if '.' in filename:
            filepart, ext = splitext(filename)
            if remove_remote_pagename:
                parts = parts._replace(path=ppath) # unsupported?
        self.urlparts = parts
        self.title = self.filepart = filepart
        self.filename, self.ext = filename.replace('/', '-'), ext
    def to_m3u(self, quote=shlex.quote, sep='\n'):
        lines = []
        y = lines.append
        y( '# %s %s' %(self.title, ('(%d)' % self.date.year) if self.date else '') )
        y( '# '+quote('/'.join(self.tags+[self.filename]).replace('\257', '_')) )
        y(str(self))
        return sep.join(lines) if sep else lines
