# This file loads the collation parameters

from .word_rank import WordRanker

common_words	= open('common_words.list', 'rU').read().split()
resolutions	= WordRanker(open('resolutions.list', 'rU').read().split('\n\n'),     bias=-6)
search_terms	= WordRanker(open('search_terms.list', 'rU').read().split('\n\n'),    bias=-5)
tag_terms	= WordRanker(open('tag_terms.list', 'rU').read().split('\n\n'),       bias=-5)
