import re
import string
import bisect
import itertools
import numpy as np
from utils import *
from sklearn.neighbors import *
from collections import defaultdict
from ddlite import Matcher, DictionaryMatch

class AllUpperNounsMatcher(Matcher):
    def __init__(self, label):
        self.label = label
        # Regex matcher to find named nouns in part-of-speech tags
        self._re_comp = re.compile("[A-Z]?NN[A-Z]?", flags=re.I)
    def apply(self, s):
        # Get parts-of-speech and words
        words = s.__dict__['words']
        pos = s.__dict__['poses']
        # Get all-cap words
        caps = set(idx for idx, w in enumerate(words) if w.upper() == w)
        # Convert character index to token index
        start_c_idx = [0]
        for s in pos:
            start_c_idx.append(start_c_idx[-1]+len(s)+1)
        # Find regex matches over phrase
        phrase = ' '.join(pos)
        for match in self._re_comp.finditer(phrase):
            # Get start index for tokens
            start = bisect.bisect(start_c_idx, match.start())-1
            # Check if word is capital, has more than two characters, and has a letter
            if start in caps and len(words[start]) > 2 and any(c.isalpha() for c in words[start]):
                yield [start], self.label

class RuleTokenizedDictionaryMatch(DictionaryMatch):
    '''Match entities using a simpler tokenizer rule than 
    what's provided by CoreNLP
    '''
    def __init__(self, label, dictionary, ignore_case=True,
                 tokenizer=lambda x:x.split()):
        super(RuleTokenizedDictionaryMatch, self).__init__(label, dictionary,
                                                             'words', ignore_case)
        self.tokenizer = tokenizer
        self.stopwords = {t:1 for t in ["on","can","is","to","a","was","at",
                                        "in","this","the","be","as","has"]}
        
    def align(self, a, b):

        #a_offsets = reduce(lambda x,y:x+y,[[i] * len(w) for i,w in enumerate(a)])
        #b_offsets = reduce(lambda x,y:x+y,[[i] * len(w) for i,w in enumerate(b)])
        a_offsets = list(itertools.chain.from_iterable([[i] * len(w) for i,w in enumerate(a)]))
        b_offsets = list(itertools.chain.from_iterable([[i] * len(w) for i,w in enumerate(b)]))
        
        mapping = {}
        for i,j in zip(a_offsets,b_offsets):
            if i not in mapping:
                mapping[i] = {}
            mapping[i][j] = 1
            
        return {i:mapping[i].keys() for i in mapping}
        
    
    def apply(self, s):
        '''
        # create offset mapping between chars and tokens
        # parser token offsets mapping top rule offsets. 
        '''
        # apply tokenizer to raw text
        seq = self.tokenizer(s.text.strip())
        offsets = [idx - s.token_idxs[0] for idx in s.token_idxs]
        tokens = unescape_penn_treebank(s.words)
        mapping = self.align(seq,tokens)
                
        # Loop over all ngrams
        for l in self.ngr:
            for i in range(0, len(seq)-l+1):
                phrase = ' '.join(seq[i:i+l])
                phrase = phrase.lower() if self.ignore_case else phrase
                
                if phrase in self.stopwords:
                    continue
                
                if phrase in self.dl[l]:
                    offsets = reduce(lambda x,y:x+y,[mapping[idx] for idx in range(i, i+l)])
                    yield list(range(min(offsets), max(offsets)+1)), self.label


        