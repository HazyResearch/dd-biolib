import os
import codecs
import cPickle
from collections import namedtuple
from .base import *
from .tools import unescape_penn_treebank
#from .utils import unescape_penn_treebank
#ddbiolib.datasets

Annotation = namedtuple('Annotation', ['text_type','start','end','text','mention_type'])

class ChemdnerCorpus(Corpus):
        
    def __init__(self, path, parser, encoding="utf-8", cache_path="/tmp/"):
        super(ChemdnerCorpus, self).__init__(path, parser, encoding)
        self.path = path
        self.cv = {"training":{},"development":{},"evaluation":{}}
        self.documents = {}
        self.annotations = {}
        
        self._load_files()
        self.cache_path = cache_path
     
    def __getitem__(self,pmid):
        """Use PMID as key and load parsed document object"""
        pkl_file = "%s/%s.pkl" % (self.cache_path, pmid)
        
        # load cached parse if it exists
        if os.path.exists(pkl_file):
            with open(pkl_file, 'rb') as f:
                self.documents[pmid] = cPickle.load(f)
        else:
            self.documents[pmid]["title"] = self.documents[pmid]["title"]
            self.documents[pmid]["body"] = self.documents[pmid]["body"]
            
            doc_str = "%s %s" % (self.documents[pmid]["title"], self.documents[pmid]["body"])
            self.documents[pmid]["sentences"] = [s for s in self.parser.parse(doc_str,doc_id=pmid)]
            
            # initialize annotations   
            self.documents[pmid]["tags"] = []
            if pmid in self.annotations:
                self.documents[pmid]["tags"] = self._label(self.annotations[pmid], self.documents[pmid]["sentences"])
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
            for i in range(len(sent_offsets)):
                start = sent_offsets[i]  
                end = sents[start].token_idxs[-1] + 1
                
                # determine span match (assume potentially overlapping spans)
                if label.start >= start and label.start <= end:
                    span = [label.start, label.start + len(label.text)]
                    
                    idx = len(sents[start].words)-1
                    for j in range(0,len(sents[start].words)-1):
                        if span[0] >= sents[start].token_idxs[j] and span[0] < sents[start].token_idxs[j+1]:
                            idx = j
                            break
                    
                    s_start = idx
                    s_end = len(sents[start].words)
                    for j in range(idx,len(sents[start].words)):
                        if span[1] > sents[start].token_idxs[j]:
                            s_end = j + 1
                        else:
                            break
                    
                    '''     
                    if label.text != " ".join(sents[start].words[s_start:s_end]):
                        print 
                        print zip(sents[start].token_idxs[s_start:],sents[start].words[s_start:])
                        print " ".join(sents[start].words[s_start:])
                        print "label:", label.text, (s_start,s_end)
                        print "text: ", " ".join(sents[start].words[s_start:s_end])
                    '''
                    #tags[i] += [ (label.text,(s_start,s_end)) ]
                    tokenized_text = " ".join(sents[start].words[s_start:s_end])
                    tags[i] += [ (tokenized_text,(s_start,s_end)) ]
    
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
            self.documents.update(docs)
        
        # load annotations
        filelist = [(x,"%s%s.annotations.txt" % (self.path,x)) for x in self.cv.keys()]
        
        for cv,fname in filelist:
            anno = [d.strip().split("\t") for d in codecs.open(fname,"r",self.encoding).readlines()]
            for item in anno:
                pmid, text_type, start, end, text, mention_type = item
                start = int(start)
                end = int(end)
                
                if pmid not in self.annotations:
                    self.annotations[pmid] = []
                
                # FIX / HACK -- in order to match candidates correctly,
                # we need sentence ids to increment properly. Parsing titles
                # and abstract bodies separately breaks ids, so we offset
                # body entities by the length of the title text
                if text_type == "A":
                    title_length = len(self.documents[pmid]["title"])
                    start +=  title_length + 1
                    end += title_length + 1
                    
                self.annotations[pmid] += [Annotation(text_type, start, end, text, mention_type)]
            