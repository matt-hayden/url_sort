#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

class WordRanker:
    def __init__(self, arg=None, **kwargs):
        self.ranks = {}
        if arg:
            self.import_tiers(arg, **kwargs)
    def __contains__(self, element):
        return element.strip().lower() in self.ranks
    def __len__(self):
        return len(self.ranks)
    def get_rank(self, token, notfound=None):
        return self.ranks.get(token.lower(), notfound)
    def import_tiers(self, tiers, bias=0):
        if isinstance(tiers, str):
            tiers = [ line for line in tiers.split('\n') if line.strip() ]
        tiers = [ t.split() if isinstance(t, str) else t for t in tiers ]
        rank = bias if (0 < bias) else len(tiers)+bias
        ranks = {}
        for tier in tiers:
            for t in tier:
                ranks[t.lower()] = rank
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
        return 'WordRanker:\n'+'\n'.join('{}={}'.format(k, v) for k,v in sorted(self.ranks.items()))
