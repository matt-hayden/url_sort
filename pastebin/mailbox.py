#! /usr/bin/env python3

import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logging.debug, logging.info, logging.warn, logging.error, logging.critical

import collections
import imaplib
import urllib.parse

import requests

import pastebin

def search_mailbox(host=None, mailbox=None, readonly=True, **kwargs):
    creds = kwargs
    with imaplib.IMAP4_SSL(host) as M:
        M.login(**creds)
        if mailbox:
            rv, [mc_s] = M.select(mailbox=mailbox, readonly=readonly)
            if rv:
                mc = int(mc_s)
                debug("%d messages", mc)
        rv, [mset] = M.search(None, '(UNSEEN)')
        mset = mset.decode().split()
        if rv == 'OK':
            for mn in mset:
                debug("Fetching message %s", mn)
                rv, message_parts = M.fetch(mn, '(RFC822)')
                if rv == 'OK':
                    envelope, _ = message_parts
                    part_num, content = envelope
                    yield [ mn, *pastebin.parse_pastebin_alert(content) ]
                else:
                    error("Message %s disappeared", mn)
        else:
            warn('No messages in search')


def apply_filter(key, **creds):
    nmatches = 0
    to_seen, to_deleted = set(), set()
    with requests.Session() as session:
        for message_number, attrs, pastes in search_mailbox(**creds):
            keyword = attrs.pop('keyword', None)
            if attrs:
                warn('Extra attributes: %s', attrs)
            for paste in pastes:
                lines = paste.fetch(session=session)
                if not lines:
                    warn("%s returned empty", paste)
                    continue
                result = key(lines=lines, \
                        keyword=keyword, \
                        paste_key=paste.paste_key)
                if result:
                    nmatches += 1
                    info("%s matches %s", paste, result)
                elif result is False:
                    to_deleted.add(message_number)
                else:
                    to_seen.add(message_number)
    if to_deleted or to_seen:
        mailbox = creds.pop('mailbox', None)
        with imaplib.IMAP4_SSL(creds.pop('host')) as M:
            M.login(**creds)
            if mailbox:
                rv, [mc_s] = M.select(mailbox=mailbox, readonly=False)
                if rv:
                    mc = int(mc_s)
                    debug("%d messages", mc)
            for mn in sorted(to_deleted, key=int):
                info("Deleting %s", mn)
                M.store(mn, '+FLAGS', '\\DELETED')
            for mn in sorted(to_seen, key=int):
                debug("Marking %s SEEN", mn)
                M.store(mn, '+FLAGS', '\\SEEN')
    return nmatches
