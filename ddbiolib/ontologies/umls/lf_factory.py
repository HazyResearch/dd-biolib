'''
Noise-aware Dictionary

Create a snapshot of all UMLS terminology, broken down by
semantic type (STY) and source vocabulary (SAB).
Treat these as competing experts, generating labeling 
functions for each

@author: jason-fries [at] stanford [dot] edu
'''
import os
import re
import bz2
import sys
import glob
import codecs
import itertools
import subprocess
from functools import partial
from collections import defaultdict
from ...utils import database
from .config import DEFAULT_UMLS_CONFIG
from .metathesaurus import MetaNorm

def dict_function_factory(dictionary,rvalue,name,ignore_case=True,stopwords={}):
    '''Dynamically create a labeling function object'''
    def function_template(m):
        mention = m.get_attrib_span('words').lower() if ignore_case else m.get_attrib_span('words')
        return rvalue if (mention in dictionary and mention not in stopwords) else 0
    function_template.__name__ = name
    return function_template


def build_umls_dictionaries(config,min_occur=1):
    '''Create UMLS dictionaries broken down by semantic type and
    source vocabulary. Term types (TTY) are used to filter out 
    obselete terms an '''
    module_path = os.path.dirname(__file__)
    filelist = glob.glob("{}/data/cache/*/*.txt".format(module_path))
    if len(filelist) > 0:
        return
    
    #mn = MetaNorm()
    
    abbrv_tty = dict.fromkeys(['AA','AB','ACR'])
    not_term_tty = dict.fromkeys(['AA','AB','ACR','AUN']) 
    
    conn = database.MySqlConn(config.host, config.username, 
                              config.dbname, config.password)
    conn.connect()
    sql_tmpl = "{}/sql_tmpl/sty_sab_dictionaries.sql".format(module_path)
    sql = "".join(open(sql_tmpl,"rU").readlines())
    
    results = conn.query(sql)
    abbrv = defaultdict(partial(defaultdict, defaultdict))
    terms = defaultdict(partial(defaultdict, defaultdict))
    
    for row in results:
        text,sty,sab,tty = row
        sty = sty.lower().replace(" ","_")
        
        # TODO: Move to interace so that this is done on reload
        #text = mn.normalize(text) # normalize to remove junk characters
        
        if tty in abbrv_tty:
            abbrv[sty][sab][text] = 1
        elif tty not in not_term_tty:
            terms[sty][sab][text] = 1
        
    for sty in abbrv:
        for sab in abbrv[sty]:
            outfname = "{}/data/cache/abbrvs/{}.{}.abbrv.txt".format(module_path,sty,sab) 
            t = sorted(abbrv[sty][sab].keys())
            if len(t) < min_occur:
                continue
            with codecs.open(outfname,"w","utf-8",errors="ignore") as f:
                f.write("\n".join(t))
            subprocess.call(["bzip2", outfname]) # compress file

    for sty in terms:
        for sab in terms[sty]:
            outfname = "{}/data/cache/terms/{}.{}.txt".format(module_path,sty,sab) 
            t = sorted(terms[sty][sab].keys())
            if len(t) < min_occur:
                continue
            with codecs.open(outfname,"w","utf-8",errors="ignore") as f:
                f.write("\n".join(t))  
            subprocess.call(["bzip2", outfname]) # compress file                
    

class UmlsNoiseAwareDict(object):
    '''Use UMLS semantic types and source vocabulary information
    to create labeling functions for providing supervision for 
    tagging tasks'''
    def __init__(self, positive=[], negative=[], name="", rm_sab=[],
                 rootdir=None, ignore_case=True, normalize=True, stopwords={}):
        
        module_path = os.path.dirname(__file__)
        self.rootdir = rootdir if rootdir else "{}/data/cache/{}/".format(module_path,name)
        self.positive = [self._norm_sty_name(x) for x in positive]
        self.negative = [self._norm_sty_name(x) for x in negative]
        self.name = name
        self.encoding = "utf-8"
        self.ignore_case = ignore_case
        self.stopwords = stopwords
        self._dictionary = self._load_dictionaries(normalize)
        self.rm_sab = rm_sab
        
    
    def _norm_sty_name(self,s):
        return s.lower().replace(" ","_")
    
    
    def _load_dictionaries(self,normalize):
        '''Load dictionaries base on provided positive/negative 
        entity examples'''
        d = defaultdict(defaultdict)
        filelist = glob.glob("{}*.txt.bz2".format(self.rootdir))
        
        mn = MetaNorm()
        
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
                    if not line.strip():
                        continue
                    try:
                        line = line.strip().decode('utf-8')
                        if normalize:
                            d_line = line
                            line = mn.apply(line)
                            # normalized form is too short -- skip
                            if len(line)/float(len(d_line)) < 0.2:
                                #print "SKIPPING", d_line, "-->", line
                                line = ""

                        
                        t = line.lower() if self.ignore_case else line
                        if t != "" and t.lower() not in self.stopwords:
                            terms += [t]
                    except:
                        print>>sys.stderr,"Warning: unicode conversion error"
                        
            if sty in d and sab in d[sty]:    
                d[sty][sab].update(dict.fromkeys(terms))
            else:
                d[sty][sab] = dict.fromkeys(terms)
            
            
            
        return d    
    
    
    def get_semantic_types(self,term):
        '''Return all matching semantic types for this term '''
        stys = {}
        for sty in self._dictionary:
            for sab in self._dictionary[sty]:
                if term in self._dictionary[sty][sab]:
                    stys[sty] = stys.get(sty,0) + 1    
        return stys
                    
    def get_dictionary(self,semantic_types=[],source_vocab=[], min_size=1):
        return self.dictionary(semantic_types,source_vocab, min_size)
                    
    def dictionary(self, semantic_types=[], source_vocab=[], min_size=1,
                   positive_only=True):
        '''Create a single dictionary building using the provided semantic types
        and source vocabularies. If either are None, use all available types. 
        '''
        # normalize semantic type names
        semantic_types = [self._norm_sty_name(x) for x in semantic_types]
        semantic_types = self._dictionary if not semantic_types else semantic_types
        sabs = list(itertools.chain.from_iterable([self._dictionary[sty].keys() for sty in self._dictionary]))
        source_vocab = dict.fromkeys(sabs) if not source_vocab else source_vocab    
        
        # filter ontologies by size and source
        d = []
        for sty in self._dictionary:
            
            if sty not in self.positive and positive_only:
                continue
            
            if sty not in semantic_types:
                continue
            
            for sab in self._dictionary[sty]:   
                if sab not in source_vocab:
                    continue
                if len(self._dictionary[sty][sab]) <= min_size:
                    continue

                d += self._dictionary[sty][sab].keys()

        return dict.fromkeys(d)
        
        
    def lfs(self, min_size=0, stopwords={}):
        '''Create labeling functions for each semantic type/source vocabulary'''
        
        for sty in self._dictionary:
            for sab in self._dictionary[sty]:
                if sab in self.rm_sab:
                    continue
                
                if len(self._dictionary[sty][sab]) <= min_size:
                    continue
                
                label = "pos" if sty in self.positive else "neg"
                prefix = "{}_".format(self.name) if self.name else ""
                func_name = "LF_{}{}_{}_{}".format(prefix,sty,sab,label)
                rvalue = 1 if label=="pos" else -1
                yield dict_function_factory(self._dictionary[sty][sab],rvalue,
                                            func_name,self.ignore_case,stopwords)
                

if __name__ == "__main__":
    # create dictionary cache 
    build_umls_dictionaries(DEFAULT_UMLS_CONFIG)             