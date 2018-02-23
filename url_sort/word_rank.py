#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import math


class WordRanker:
    def __init__(self, arg=None, **kwargs):
        self.ranks = {}
        if arg:
            if isinstance(arg, str):
                tiers = [ line for line in arg.split('\n') if line.strip() ]
            else:
                tiers = arg
            self.import_tiers(tiers, **kwargs)
    def __contains__(self, element):
        return element.strip().lower() in self.ranks
    def __len__(self):
        return len(self.ranks)
    def get_rank(self, token, notfound=None):
        return self.ranks.get(token.lower(), notfound)
    def import_tiers(self, tiers, bias=0):
        tiers = [ t.split() if isinstance(t, str) else t for t in tiers ]
        rank = bias if (0 < bias) else len(tiers)+bias
        ranks = {}
        for tier in tiers:
            n_subtiers = len(tier)
            places = 1+round(math.log10(n_subtiers)) if (1 < n_subtiers) else 0.
            dsubrank = 10**-places
            subrank = float(rank)
            for t in tier:
                ranks[t.lower()] = subrank
                subrank += dsubrank
            rank -= 1
        self.ranks = ranks
    def replace_tokens(self, tokens, reducer=lambda a,b: a+b, score=0):
        not_found = []
        for t in tokens:
            if (t in self):
                score = reducer(self.get_rank(t), score)
            else:
                not_found.append(t)
        return score, not_found
    def __str__(self):
        return 'WordRanker:\n' \
                +'\n'.join('{}={:.2f}'.format(k, v) for k,v in sorted(self.ranks.items()))
