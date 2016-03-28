import cPickle
from datasets import *
from collections import namedtuple
import sys
from utils import unescape_penn_treebank

Annotation = namedtuple('Annotation', 'text_type start end text mention_type')

def align(a, b):
    '''Align sequences and return mapped offsets'''
    j = 0
    offsets = []
    for i in range(0,len(a)):
        if a[i] in [" "]:
            continue
      
        matched = False
        while not matched and j < len(b):
            if a[i] == b[j]:
                offsets += [(i,j,a[i],b[j])]
                matched = True
            j += 1
            
    return offsets


def token_mapping(doc,tokens):
        '''
        Create a character-level mapping from a raw, unparsed document
        to a parsed and tokenized document
        '''  
        tokenized = " ".join(reduce(lambda x,y:x+y,tokens))
        offsets = align(tokenized, doc)
        token_idx, doc_idx, token_ch, doc_ch = zip(*offsets)
        
        return dict(zip(doc_idx,token_idx))

        
class ChemdnerCorpus(Corpus):
        
    def __init__(self, path, parser, cache_path="/tmp/"):
        super(ChemdnerCorpus, self).__init__(path, parser)
        self.path = path
        self.cv = {"training":{},"development":{},"evaluation":{}}
        self.documents = {}
        self.annotations = {}
        
        self._load_files()
        self.cache_path = cache_path
    
    
    def __build_charmap(self,pmid):
        ''' DEPRICATED (doesn't work)
        '''
        if pmid not in self.annotations:
            return {}
        
        doc = self.documents[pmid]["title"].strip() + " " + self.documents[pmid]["body"].strip()
        tokenized = []
        for sent in self.documents[pmid]["sentences"]:
            tokenized += [unescape_penn_treebank(sent.words)]
        
        mapping = token_mapping(doc,tokenized)
        tokenized = " ".join([" ".join(sent) for sent in tokenized])
        
        
    def __getitem__(self,pmid):
        """Use PMID as key and load parsed document object"""
        pkl_file = "%s/%s.pkl" % (self.cache_path, pmid)
        
        # load cached parse if it exists
        if os.path.exists(pkl_file):
            with open(pkl_file, 'rb') as f:
                self.documents[pmid] = cPickle.load(f)
        else:
            title = [s for s in self.parser.parse(self.documents[pmid]["title"])]
            body = [s for s in self.parser.parse(self.documents[pmid]["body"])]
            self.documents[pmid]["sentences"] = title + body
            
            # create mapping char_idx->token_idx
            #if self.annotations[pmid]:
            #    self.__build_charmap(pmid)
                
            with open(pkl_file, 'w+') as f:
                cPickle.dump(self.documents[pmid], f)
    
        return self.documents[pmid]
        
    
    def __iter__(self):
        
        for pmid in self.documents:
            yield self.__getitem__(pmid)
            
        
    def _load_files(self):
        '''
        ChemDNER corpus format (tab delimited)
        1- Article identifier (PMID)
        2- Type of text from which the annotation was derived (T: Title, A: Abstract)
        3- Start offset
        4- End offset
        5- Text string of the entity mention
        6- Type of chemical entity mention (ABBREVIATION,FAMILY,FORMULA,IDENTIFIERS,MULTIPLE,SYSTEMATIC,TRIVIAL)
        '''
        filelist = [(x,"%s%s.abstracts.txt" % (self.path,x)) for x in self.cv.keys()]
        for cv,fname in filelist:
            docs = [d.strip().split("\t") for d in open(fname,"r").readlines()]
            docs = {pmid:{"title":title,"body":body} for pmid,title,body in docs}
            self.cv[cv] = {pmid:1 for pmid in docs} 
            self.documents.update(docs)
        
        # load annotations
        filelist = [(x,"%s%s.annotations.txt" % (self.path,x)) for x in self.cv.keys()]
        for cv,fname in filelist:
            anno = [d.strip().split("\t") for d in open(fname,"r").readlines()]
           
            for item in anno:
                pmid, text_type, start, end, text, mention_type = item
                start = int(start)
                end = int(end)
                if pmid not in self.annotations:
                    self.annotations[pmid] = []
                self.annotations[pmid] += [Annotation(text_type, start, end, text, mention_type)]
            