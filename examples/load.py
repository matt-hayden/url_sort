# Example file for loading the collation parameters

from url_sort.word_rank import *

# simplist possible word list:
common_words	= open('common_words.list', 'rU').read().split()

# These are double-newline separated lists of lists. The bias
# argument places neutral sort +N places from the top of the sort
# or -N places from the bottom.
resolutions     = read_wordranks('resolutions.list',  bias=-6)
# or, folders of such
search_terms    = read_wordranks('search_terms.d',    bias=-6)
tag_terms       = read_wordranks('tag_terms.list',    bias=-5)

if __name__ == '__main__':
    print(resolutions)
    print(search_terms)
    print(tag_terms)
