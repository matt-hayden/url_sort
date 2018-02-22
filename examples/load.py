# This file loads the collation parameters

from url_sort.word_rank import WordRanker

def read_wordranks(*args, sep='\n\n', **kwargs):
    contents = []
    for arg in args:
        contents += open(arg, 'rU').read().split(sep)
    return WordRanker(contents, **kwargs)


# simplist possible word list:
common_words	= open('common_words.list', 'rU').read().split()

# these are double-newline separated lists of lists
resolutions     = read_wordranks('resolutions.list',  bias=-8)
search_terms    = read_wordranks('search_terms.list', bias=-5)
tag_terms       = read_wordranks('tag_terms.list',    bias=-5)
