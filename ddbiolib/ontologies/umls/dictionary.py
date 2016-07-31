'''
UMLS Dictionary

TODO: all dictionaries should be persisted in Snorkel's 
eventual "context" ORM interface

@author: jason-fries [at] stanford [dot] edu
'''
import os
import re
import bz2
import sys
import glob
import codecs
import itertools
from functools import partial
from collections import defaultdict
from .metathesaurus import MetaNorm

class UmlsDictionary(object):

    def __init__(self, term_type="*", sem_types=[], 
                 source_vocabs=[], rootdir=None, ignore_case=False):
        '''UMLS dictionary
        
        Load cached dictionary files broken down by semantic type (sty), 
        source vocabulary (sab), and term type (abbrvs|terms)
        
        Parameters
        ----------
        term_type : str
            abbrvs|terms|*, Default * is to load both
            
        sem_types : array, optional
            List of semantic types to load. Default is to load all.
            
        source_vocabs : array, optional
            Source input vocabularies. Default is to load all.
        
        rootdir : string, optional
            Source directory for cached dictionaries
            
        ignore_case : boolean, optional
            Lowercase all text if True, default = False
        
        Attributes
        ----------
        
            
        Examples
        --------
        
        '''
        module_path = os.path.dirname(__file__)
        self.rootdir = rootdir if rootdir else "{}/data/cache/{}/".format(module_path,term_type)
        
        self.term_type = term_type
        self.sem_types = [self._norm_sty_name(s) for s in sem_types]
        self.source_vocabs = source_vocabs
        self.encoding = "utf-8"
        self.ignore_case = ignore_case
        
        self._dictionary = self._load_dictionaries()

        
    def _norm_sty_name(self,s):
        return s.lower().replace(" ","_")
    

    def _load_dictionaries(self):
        '''Load dictionaries'''
        d = defaultdict(defaultdict)
        filelist = glob.glob("{}*.txt.bz2".format(self.rootdir))
        
        for fpath in filelist:
            fname = fpath.split("/")[-1].rstrip(".txt.bz2")
            i = fname.index(".")
            sty,sab = fname[0:i], fname[i+1:].rstrip(".abbrv")
            
            # only include specified semantic types and source vocabularies
            if self.sem_types and sty not in self.sem_types:
                continue
            if self.source_vocabs and sab not in self.source_vocabs:
                continue

            terms = []
            with bz2.BZ2File(fpath,"rb") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        line = line.strip().decode('utf-8')
                        terms += [line.strip().lower() if self.ignore_case else line.strip()]
                    except:
                        print>>sys.stderr,"Warning: unicode conversion error"
                        
            if sty in d and sab in d[sty]:    
                d[sty][sab].update(dict.fromkeys(terms))
            else:
                d[sty][sab] = dict.fromkeys(terms)
            
        return d    
    
    
    def get_sem_types(self,term):
        '''Return all matching semantic types for this term '''
        stys = {}
        for sty in self._dictionary:
            for sab in self._dictionary[sty]:
                if term in self._dictionary[sty][sab]:
                    stys[sty] = stys.get(sty,0) + 1    
        return stys
    
    
    def coverage(self,terms,ignore_case=True):
        '''Score a list of terms by source dictionary coverage. We're
        not doing a set cover optimization, just returning a ranked list
        of percent covered by dictionary sty/sab'''
        scores = {}
        terms = [t.lower() if ignore_case else t for t in terms]
        for sty in self._dictionary:
            for sab in self._dictionary[sty]:
                #dictionary = [t.lower() if ignore_case else t for t in self._dictionary[sty][sab]]
                dictionary = self._dictionary[sty][sab]
                intersection = sum([1 for t in terms if t in dictionary])
                if intersection > 0:
                    scores[(sty,sab)] = intersection / float(len(terms))  
        return sorted(scores.items(),key=lambda x:x[1], reverse=1)
                        
                             
    def get_dictionary(self):
        '''Collapse into single dictionary'''
        # normalize semantic type names
        d = [[self._dictionary[sty][sab].keys() for sab in self._dictionary[sty]] for sty in self._dictionary]
        d = map(lambda x:list(itertools.chain.from_iterable(x)),d)
        return dict.fromkeys(itertools.chain.from_iterable(d))
                

if __name__ == "__main__":
   
    abbrvs = UmlsDictionary("abbrvs",sem_types=["Disease or Syndrome"])
    terms = UmlsDictionary("terms",sem_types=["Disease or Syndrome"],
                          source_vocabs=['SNOMEDCT_US'])
    d = terms.get_dictionary()
    print len(d)
    
    
    
    
    