#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

from datetime import datetime
import re

current_year = datetime.now().year


def get_year_parser(text, *args, \
    YYYYMM      = re.compile('(?:[^0-9])(?P<year>(19|20)\d\d)'), \
    XX_MM_XX    = re.compile('(?:[^\d])(\d\d)([._])(\d\d)\\2(\d\d)(?:[^d]|$)'), \
    XXMMXX      = re.compile('(?:[^\d])(\d\d)(\d\d)(\d\d)(?:[^\d]|$)') ):
    m = YYYYMM.search(text) # only first occurrance is tested
    if m:
        regex = YYYYMM
        y = int(m.group('year'))
        if (1920 < y < current_year):
            return y, regex
    Y = M = D = None
    m = XX_MM_XX.search(text)
    if m:
        regex = XX_MM_XX
        Y = int(m.group(1))
        # Months is 3
        D = int(m.group(4))
    else:
        m = XXMMXX.search(text)
        if m:
            regex = XXMMXX
            Y = int(m.group(1))
            D = int(m.group(3))
    if Y or D:
        if (70 <= Y <= 99):
            return 1900+Y, regex
        if (0 <= Y <= 18):
            return 2000+Y, regex
        Y, D = D, Y
        if (70 <= Y <= 99):
            return 1900+Y, regex
        if (0 <= Y <= 18):
            return 2000+Y, regex
    return None, None
