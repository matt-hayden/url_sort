#! /usr/bin/env python3
"""
Example of loading python modules from the current directory.
WARNING: not necessarily a _good_ example.
"""

import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import importlib
import os, os.path
import sys


sys.path.insert(0, os.path.abspath('.'))
config_mod_name = 'load'
search_config	= importlib.import_module(config_mod_name, '.')
debug(          "Loaded search config from '%s'", str(search_config))
common_words	= search_config.common_words
info(		"{} common words".format(len(common_words)) )
resolutions	= search_config.resolutions
info(		"resolutions: {}".format(resolutions) )
search_terms	= search_config.search_terms
info(		"search_terms: {}".format(search_terms) )
tag_terms	= search_config.tag_terms
info(		"tag_terms: {}".format(tag_terms) )
