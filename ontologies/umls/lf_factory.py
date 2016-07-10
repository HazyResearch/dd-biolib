'''
Noise-aware Dictionary

@author: jason-fries
'''
import re
import bz2
import glob
import codecs
from collections import defaultdict


def dict_function_factory(dictionary,rvalue,name,ignore_case=True):
    
    def function_template(m):
        mention = " ".join(m.mention()).lower() if ignore_case else " ".join(m.mention())
        return rvalue if mention in dictionary else 0
    function_template.__name__ = name
    return function_template


class UmlsNoiseAwareDict(object):
    def __init__(self, positive=[], negative=[], prefix="",
                 rootdir="", ignore_case=True):
        ''' '''
        self.positive = [self._norm_sty_name(x) for x in positive]
        self.negative = [self._norm_sty_name(x) for x in negative]
        self.rootdir = rootdir
        self.prefix = prefix
        self.encoding = "utf-8"
        self.ignore_case = ignore_case
        self.dictionary = self._load_dictionaries()
        
    def _norm_sty_name(self,s):
        return s.lower().replace(" ","_")
    
    def _load_dictionaries(self):
        ''' '''
        d = defaultdict(defaultdict)
        filelist = glob.glob("{}*.txt.bz2".format(self.rootdir))
    
        for fpath in filelist:
            fname = fpath.split("/")[-1].rstrip(".txt.bz2")
            i = fname.index(".")
            sty,sab = fname[0:i], fname[i+1:].rstrip(".abbrv")
            dict_type = "terms" if "abbrv" not in fname else "abbrv"
            
            # skip semantic types we don't flag as postive of negative
            if sty not in self.positive and sty not in self.negative:
                continue
            
            terms = []
            with bz2.BZ2File(fpath,"rb") as f:
                for line in f:
                    terms += [line.strip().lower() if self.ignore_case else line.strip()]
                    
            d[sty][sab] = dict.fromkeys(terms)
            #print sty,sab,dict_type, len(d[sty][sab]), d[sty][sab].keys()[0:10]
        return d    
                
    def lfs(self):
        
        for sty in self.dictionary:
            for sab in self.dictionary[sty]:
                label = "pos" if sty in self.positive else "neg"
                prefix = "{}_".format(self.prefix) if self.prefix else ""
                func_name = "LF_{}{}_{}_{}".format(prefix,sty,sab,label)
                rvalue = 1 if label=="pos" else -1
                yield dict_function_factory(self.dictionary[sty][sab],rvalue,
                                            func_name,self.ignore_case)
                
                