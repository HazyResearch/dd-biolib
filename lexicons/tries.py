'''
Created on Jun 28, 2013

@author: fries
'''

import marisa_trie
import re

class TrieLexicon(object):
    """Given an input lexicon, label each term as a match or not. 
    Implementation uses a prefix trie for matching:
    https://github.com/kmike/marisa-trie
    
    """
    def __init__(self, lexicon, label, encoding='utf-8'):
        """
        :param lexicon: path to tab delimited (classname,value) term lexicon
        :param label: name for feature column field header
        :param encoding: marisa trie requires unicode key text
        """
        self.name = label
        self.encoding = encoding
        self.lexicon = lexicon
        self.trie = marisa_trie.Trie(lexicon)
        
        self.lexicon_srt = {}
        for phrase in self.lexicon:
            length = len(phrase.split())
            if length not in self.lexicon_srt:
                self.lexicon_srt[length] = {}
            self.lexicon_srt[length][phrase] = 1
 
        self.max_ngram_len = 3

    def __max_str_match(self, candidates, seq):
        """Given a set of candidate matches and a seq from a document,
        find the longest exact match.
        :param condidates: prefix key matches from trie
        :param seq: token seq from a sentence in the current document
        
        """
        for termset in candidates:
            match = True
            if len(seq) >= len(termset):
                span = [t for t in seq[0:len(termset)]]
                span = zip(span,termset)
                for item in span:
                    if not match:
                        break
                    match = item[0] == item[1]
                                
                if match:
                    return termset
        
        return None
        
    
    def __get_match(self,seq):
       
        term = seq[0]
       
        # term prefixes
        m = self.trie.keys(term)
    
        if len(m) == 0:
            return None
        
        # sort matches; we want the longest phrase match possible
        m = [x.split() for x in m]
        m.sort(key=len,reverse=True)
        
        # candidate match
        match = None
        
        # is this term in the trie
        if term in self.trie:
           
            # possible longer phrase match
            if len(m) > 1:
                      
                match = self.__max_str_match(m,seq)
                if match:
                    match = " ".join(match)
                        
            # only 1 match
            else:
                match = term
                
        # check to see if this is a prefix of a longer match
        # ( non-matching subterms are *not* entered in the trie,
        # e.g., take "middle eastern", "middle" is not in the trie
        # as a keyed match, since it doesn't link directly to a
        # race definition )
        else:
            
            match = self.__max_str_match(m, seq)
     
            if match:
                match = " ".join(match)
                
        return match
    
    '''
    def prefix_search(self,doc):
        
        #if self.trie.trie.has_keys_with_prefix(doc):
        print doc
        return self.trie.trie.keys(doc)
        #else:
        #    return []
    '''
    
    def search(self,doc):
        """Keep the longest exact match for an item in our lexicon
        """     
        matches = []
        for i in range(len(doc)):
        
            match = self.__get_match(doc[i:])
            if match:
                matches += [match]
                    
        return matches
    
    
    def match(self,doc):
        
        spans = {}
        matches = []
        claimed = [0] * len(doc)
        
        
        for length in range(self.max_ngram_len,1,-1):
            
            for i in range(len(doc)):        
                phrase = " ".join(doc[i:i+length])
                
                if phrase in self.lexicon_srt[length]:
                    
                    # TODO: ignore longer matches
                    if sum(claimed[i:i+length]) != 0:
                        continue
                    
                    for j in range(i,i+length):
                        spans[j] = len(matches)
                        
                    claimed[i:i+length] = [1] * length
                    matches += [(phrase,(i,i+length))]
                    
                    
                    
                   
        return matches,spans

