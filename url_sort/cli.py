#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import fileinput

from .parser import sort_urls

def main():
    print( '\n'.join(sort_urls(fileinput.input())) )
