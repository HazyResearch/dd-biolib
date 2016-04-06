import sys
import codecs
import cPickle
from datasets import *
from collections import namedtuple
from utils import unescape_penn_treebank

Annotation = namedtuple('Annotation', ['text_type','start','end','text','mention_type'])

class ChemdnerCorpus(Corpus):
        
    def __init__(self, path, parser, cache_path="/tmp/"):
        super(ChemdnerCorpus, self).__init__(path, parser)
        self.path = path
        self.cv = {"training":{},"development":{},"evaluation":{}}
        self.documents = {}
        self.annotations = {}
        self.encoding = "utf-8"
        self.verbose = True
        
        self._load_files()
        self.cache_path = cache_path
        if not os.path.exists(cache_path):
            pass
     
    def __getitem__(self,pmid):
        """Use PMID as key and load parsed document object"""
        pkl_file = "%s/%s.pkl" % (self.cache_path, pmid)
        # load cached parse if it exists
        if os.path.exists(pkl_file):
            with open(pkl_file, 'rb') as f:
                self.documents[pmid] = cPickle.load(f)
        else:
            self.documents[pmid]["title"] = self.documents[pmid]["title"].encode("ascii","ignore")
            self.documents[pmid]["body"] = self.documents[pmid]["body"].encode("ascii","ignore")
            
            title = [s for s in self.parser.parse(self.documents[pmid]["title"])]
            body = [s for s in self.parser.parse(self.documents[pmid]["body"])]
            #print type(self.documents[pmid]["title"]), type(self.documents[pmid]["body"])
            
            # initialize annotations   
            self.documents[pmid]["tags"] = []
            self.documents[pmid]["sentences"] = title + body
            
            if pmid in self.annotations:
                title_labels = [label for label in self.annotations[pmid] if label.text_type=='T']
                body_labels = [label for label in self.annotations[pmid] if label.text_type=='A']
                self.documents[pmid]["tags"] = self._label(title_labels,title)
                self.documents[pmid]["tags"] += self._label(body_labels,body)
            else:
                self.documents[pmid]["tags"] += [[] for _ in range(len(self.documents[pmid]["sentences"]))]
 
            with open(pkl_file, 'w+') as f:
                cPickle.dump(self.documents[pmid], f)
        
        return self.documents[pmid]
           
    def _label(self,annotations,sentences):
        '''Convert annotations from ChemNDER offsets to parsed token offsets. 
        NOTE: This isn't perfect, since tokenization can fail to correctly split
        some tags. 
        '''
        tags = [[] for i,_ in enumerate(sentences)]
        
        sents = {min(sent.token_idxs):sent for sent in sentences}
        sent_offsets = sorted(sents)
        
        for label in annotations:
            # find target sentence
            for i in range(len(sent_offsets)):
                start = sent_offsets[i]  
                end = sents[start].token_idxs[-1] + 1
                
                if label.start >= start and label.start < end:
                    span = [label.start, label.start + len(label.text)]
                    # determine span match
                    idx = -1
                    s_end = sents[start].token_idxs[-1]
                    while s_end >= span[1]:
                        idx = idx - 1
                        s_end = sents[start].token_idxs[idx]
                
                    s_start = sents[start].token_idxs[idx]
                    while s_start > span[0]:
                        idx = idx - 1
                        s_start = sents[start].token_idxs[idx]  
                    
                    ii = sents[start].token_idxs.index(s_start)
                    jj = sents[start].token_idxs.index(s_end)
                    tags[i] += [ (label.text,(ii,jj+1)) ]
                 
        return tags           

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
            docs = [d.strip().split("\t") for d in codecs.open(fname,"r",self.encoding).readlines()]
            docs = {pmid:{"title":title,"body":body} for pmid,title,body in docs}
            self.cv[cv] = {pmid:1 for pmid in docs} 
            self.documentsw.update(docs)
        
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
            