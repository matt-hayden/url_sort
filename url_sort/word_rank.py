#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
import math

from .util import *


def read_wordranks(*args, sep='\n\n', **kwargs):
    contents = []
    y = contents.extend
    for arg in expand_dirs(*args):
        y(open(arg, 'rU').read().split(sep))
    return WordRanker(contents, **kwargs)


class WordRanker:
    """
    From an iterable of iterables, or newline-separated strings.
    """
    tier_sep = '\n'
    def __init__(self, arg=None, **kwargs):
        self.ranks = collections.OrderedDict()
        if arg:
            if isinstance(arg, str):
                tiers = [ line for line in arg.split(self.tier_sep) if line.strip() ]
            else:
                tiers = arg
            self.import_tiers(tiers, **kwargs)
    def __contains__(self, element):
        return element.strip().lower() in self.ranks
    def __len__(self):
        return len(self.ranks)
    def get_rank(self, token, notfound=None):
        return self.ranks.get(token.lower(), notfound)
    def _import_tiers(self, tiers, bias=0):
        rank = bias if (0 < bias) else len(tiers)+bias
        ranks = {}
        for tier in tiers:
            n_subtiers = len(tier)
            places = 1+round(math.log10(n_subtiers)) if (1 < n_subtiers) else 0.
            dsubrank = 10**-places
            subrank = float(rank)
            for t in tier:
                ranks[t.lower().replace('_', '\0')] = subrank
                subrank += dsubrank
            rank -= 1
        self.ranks = ranks
    def import_tiers(self, tiers, **kwargs):
        tiers = [ t.split() if isinstance(t, str) else t for t in tiers ]
        return self._import_tiers(tiers, **kwargs)
    def get_compound_tokens(self):
        return { t.lower(): score for t, score in self.ranks.items() if ('\0' in t) }
    def replace_terms(self, terms, reducer=sum):
        scores_found, not_found = [], []
        compound_tokens = self.get_compound_tokens()
        if compound_tokens:
            zterms = '\0'.join(terms)
            for ct in compound_tokens:
                if ct in zterms.lower():
                    scores_found.append((compound_tokens[ct], ct))
                    zterms = case_insensitive_replace(zterms, ct, '')
            terms = filter(None, zterms.split('\0'))
        for t in terms:
            if (t in self):
                scores_found.append((self.get_rank(t), t))
            else:
                not_found.append(t)
        scores_found.sort()
        return reducer(score for score, t in scores_found) if scores_found else None, \
                [ t for score, t in scores_found ], \
                not_found
    def __str__(self):
        return 'WordRanker:\n' \
                +'\n'.join('{}={:.2f}'.format(k.replace('\0', '\u00A4'), v) for k,v in sorted(self.ranks.items()))


if __name__ == '__main__':
    print(case_insensitive_replace('ONE FISH TWO FISH RED FISH BLUE FISH', 'fIsH', 'foosh'))
