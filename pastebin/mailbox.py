#! /usr/bin/env python3

import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logging.debug, logging.info, logging.warn, logging.error, logging.critical

import collections
import imaplib
import urllib.parse

import requests

from .pastebin import parse_pastebin_alert
import url_sort.parser

def search_mailbox(host=None, mailbox=None, latest=None, **kwargs):
    creds = kwargs
    if latest:
        latest = int(latest)
    assert 0 < latest
    with imaplib.IMAP4_SSL(host) as M:
        M.login(**creds)
        if mailbox:
            rv, [mc_s] = M.select(mailbox=mailbox, readonly=True)
            if rv:
                mc = int(mc_s)
                debug("%d messages", mc)
        rv, [mset] = M.search(None, '(UNSEEN)')
        mset = mset.decode().split()
        if rv == 'OK':
            if latest:
                mset = sorted(mset, key=lambda s: -int(s))
                mset = mset[:latest]
            for mn in mset:
                debug("Fetching message %s", mn)
                rv, message_parts = M.fetch(mn, '(RFC822)')
                if rv == 'OK':
                    envelope, _ = message_parts
                    part_num, content = envelope
                    d = parse_pastebin_alert(content)
                    d['message_number'] = mn
                    yield d
                else:
                    error("Message %s disappeared", mn)
        else:
            warn('No messages in search')


def apply_filter(key=None, safe=False, **kwargs):
    payload = None
    if key is None:
        payload = DefaultFilter()
        debug("Using default filter %s", payload)
        key = payload.mailbox_key
    assert callable(key)
    """
        key should return three possibilities:
            False   message will be deleted
            None    message will be unseen
            truthy  message will be seen
        key is called with:
            lines       an iterable of strings
            keyword     usually the original search term
            paste_key   pastebin id
    """
    tri = lambda v: { False: -1, None: 0, True: 1}[bool(v)]
    nmatches = 0
    to_seen, to_deleted = set(), set()
    with requests.Session() as session:
        for pastebin_message in search_mailbox(**kwargs):
            message_number = pastebin_message.pop('message_number')
            # Move key-values from the attrs list into the dict object
            # If multiple keywords exist (unlikely) only one will survive!
            attrs = dict(pastebin_message.pop('attrs'))
            pastebin_message.update(attrs)
            #
            pastes = pastebin_message.pop('links')
            message_result = False
            for paste in pastes:
                lines = paste.fetch(session=session)
                if not lines:
                    info("%s returned empty", paste)
                    continue
                result = key(lines=lines, \
                        paste_key=paste.paste_key, **pastebin_message)
                if result:
                    nmatches += 1
                    info("%s matches %s", paste, result)
                message_result = max(message_result, result, key=tri)
            if message_result == 'url list': # TODO
                to_seen.add(message_number)
            elif message_result is None:
                debug("Ignoring message number %s", message_number)
            elif message_result is False:
                debug("Marking message number %s (%s) for deletion", message_number, pastebin_message['date'])
                to_deleted.add(message_number)
    creds = kwargs
    if to_deleted or to_seen:
        mailbox = creds.pop('mailbox', None)
        with imaplib.IMAP4_SSL(creds.pop('host')) as M:
            M.login(creds.pop('user'), creds.pop('password'))
            if mailbox:
                rv, [mc_s] = M.select(mailbox=mailbox, readonly=bool(safe))
                if rv:
                    mc = int(mc_s)
                    debug("%d messages", mc)
            if to_deleted:
                warn("Deleting %s messages", len(to_deleted))
                for mn in sorted(to_deleted, key=int):
                    info("Deleting %s", mn)
                    M.store(mn, '+FLAGS', '\\DELETED')
            if to_seen:
                info("Marking %d messages read", len(to_seen))
                for mn in sorted(to_seen, key=int):
                    debug("Marking %s SEEN", mn)
                    M.store(mn, '+FLAGS', '\\SEEN')
    return nmatches, payload


class FilterBase:
    """
    Abstract. Please override .mailbox_key()
    """
    def __init__(self):
        self.contents = collections.defaultdict(list)
    def __len__(self):
        return len(self.contents)
    def __bool__(self):
        return 0 < len(self)
class DefaultFilter(FilterBase):
    """
    This class contains the logic to distinguish useful paste content from
    spam. 
    """
    stopwords = '127.0.0.1 powerfiler.com swporn urlin.us'.split()
    def mailbox_key(self, lines, **kwargs):
        """
        Intended as an argument for pastebin:mailbox.apply_filter
        """
        nlinks = 0
        for n, line in enumerate(lines, start=1):
            if ('EXTM3U') in line or ('EXTINF' in line):
                self.contents['m3u'].append(lines)
                return 'm3u'
            if 'Copy & Paste link' in line:
                return False
            line = line.lower()
            if ('//' in line) or ('http' in line):
                nlinks += 1
                if '.onion' in line:
                    self.contents['tor'].append(lines)
                    return 'tor'
                if 'openload' in line:
                    self.contents['url list'].append(lines)
                    return 'url list'
            if any(s in line for s in self.stopwords):
                debug("stopword caught message")
                return False
        if nlinks < 1:
            error("Message has no links")
            return False
    def process_url_lists(self, sep='\n\n', **kwargs):
        if self.contents.get('url list', None):
            urls = url_sort.parser.sort_urls(*self.contents['url list'], **kwargs)
            return sep.join(u.to_m3u() for u in urls)
        return ''
