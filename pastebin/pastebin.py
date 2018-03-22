#! /usr/bin/env python3

import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logging.debug, logging.info, logging.warn, logging.error, logging.critical

import collections
import email.parser
import html.parser
import urllib.parse

import requests

contents_memo = {}

class PastebinPaste:
    def __init__(self, arg, **kwargs):
        self.__dict__.update(kwargs)
        if isinstance(arg, str):
            url = urllib.parse.urlsplit(text)
        else:
            url = arg
        if url.path:
            self.paste_key = url.path.lstrip('/')
    def __repr__(self):
        return self.paste_key
    def __str__(self):
        return urllib.parse.urlunsplit(('https', 'pastebin.com', self.paste_key, None, None))
    def get_raw_url(self):
        return urllib.parse.urlunsplit(('https', 'pastebin.com', 'raw/'+self.paste_key, None, None))
    def fetch(self, session=None):
        if self.paste_key not in contents_memo:
            url = self.get_raw_url()
            if session:
                req = session.get(url)
            else:
                req = requests.get(url)
            if req.ok:
                contents_memo[self.paste_key] = req.text.splitlines()
        return contents_memo.get(self.paste_key, None)


class PastebinAlertParser(html.parser.HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.links = []
    def __str__(self):
        return "<pastebin(s) %s>" %(', '.join(l.paste_key for l in self.links))
    def handle_starttag(self, tag, attrs):
        if tag in 'a img'.split():
            dattrs = collections.OrderedDict(attrs)
            if dattrs.get('href', None):
                url = urllib.parse.urlsplit(dattrs['href'])
                if url.hostname == 'pastebin.com':
                    self.links.append(PastebinPaste(url))
            else:
                warn("Ignored link %s %s", tag, attrs)
        elif tag not in 'br'.split():
            debug("Ignoring %s %s", tag, attrs)


def parse_pastebin_alert(content, parser=email.parser.BytesParser()):
    def parse_subject_line(text):
        tokens = text.split(',')
        assert tokens.pop(0).strip() == 'Pastebin.com Alerts Notification'
        for t in tokens:
            if ':' in t:
                k, v = t.split(':', 1)
            else:
                k, v = t, True
            yield k.strip(), v.strip()
    m = parser.parsebytes(content)
    p = PastebinAlertParser()
    for part in m.walk():
        if part.get_content_type() == 'text/html':
            p.feed(part.get_payload())
    return { 'links': p.links, 'date': m['date'], \
             'attrs': list(parse_subject_line(m['subject'])) }
