import os
import re
import sys
import glob
import codecs
import subprocess
from collections import namedtuple
from ..utils import download
from ..corpora import Corpus,Document,DocParser
from ..parsers import PickleSerializedParser


class Annotation(object):
    
    def __init__(self, text_type, start, end, text, mention_type):
        self.text_type = text_type
        self.start = start
        self.end = end
        self.text = text
        self.mention_type = mention_type

    def __str__(self):
        return "Annotation(start={}, end={}, text={})".format(self.start,self.end,self.text)

def align(a, b):
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
            
    token_idx, doc_idx, token_ch, doc_ch = zip(*offsets)
    #return offsets,dict(zip(doc_idx,token_idx))
    return offsets,dict(zip(token_idx,doc_idx))

class CdrParser(DocParser):
    '''
        The CDR disease corpus 
                             -- f                    
        1500 PubMed abstracts
        X disease mentions
        X chemical mentions
    '''
    def __init__(self, inputpath=None, entity_type="Disease", split_chars=[]):
        super(CdrParser, self).__init__(inputpath, "utf-8")
        self.split_chars = split_chars
        if not inputpath:
            self.inputpath = "{}/data/CDR.Corpus.v010516/".format(os.path.dirname(__file__))
        else:
            self.inputpath = inputpath
        self._docs = {}
        # download CDR data
        if not os.path.exists(self.inputpath):
            self._download()
        self._preload(entity_type)
        
    def _download(self):
        print>>sys.stderr,"CDR files require a Biocreative account. See http://www.biocreative.org/accounts/register/"

    def _preload(self, et):
        '''Load entire corpus into memory'''
        
        
        cvdefs = {"CDR_DevelopmentSet.PubTator.txt":"development",
                  "CDR_TestSet.PubTator.txt":"testing",
                  "CDR_TrainingSet.PubTator.txt":"training"}
        
        filelist = glob.glob("%s/*.txt" % self.inputpath)

        for fname in filelist:
            setname = cvdefs[fname.split("/")[-1]]
            documents = []
            with codecs.open(fname,"rU",self.encoding) as f:
                doc = []
                for line in f:
                    row = line.strip()
                    if not row and doc:
                        documents += [doc]
                        doc = []
                    elif row:
                        row = row.split("|") if (len(row.split("|")) > 1 and 
                                                 row.split("|")[1] in ["t","a"]) else row.split("\t")
                        doc += [row]
                if doc:
                    documents += [doc]

            for doc in documents:
                pmid,title,abstract = doc[0][0],doc[0][2],doc[1][2]
                text = "%s %s" % (title, abstract)
                
                attributes = {"set":setname,"title":title,"abstract":abstract}            
                attributes["annotations"] = []
                
                # load annotation tuples
                for row in doc[2:]:
                    
                    # relation
                    # ----------------------------
                    if len(row) <= 4:# or row[4] == "Chemical":
                        pmid,rela,m1,m2 = row
                        continue
                    
                    # entity
                    # ----------------------------
                    if len(row) == 6:
                        pmid, start, end, mention, mention_type, duid = row
                        norm_names = []
                    elif len(row) == 7:
                        pmid, start, end, mention, mention_type, duid, norm_names = row
                    duid = duid.split("|")
                    
                    start,end = int(start),int(end)
                    text_type = "T" if end <= len(title) else "A"

                    if mention_type != et:
                        continue
                    label = Annotation(text_type, start, end, mention, mention_type)
                    attributes["annotations"] += [label]
                
                #
                # Force tokenization on certain characters BEFORE parsing
                #
                if self.split_chars:
                    rgx = "([{}])".format("".join(self.split_chars))
                    t_text = re.sub(rgx, r" \1 ", text)
                    t_text = re.sub("\s{2,}"," ",t_text)
                    text += " " * (len(t_text) - len(text))
                    _, char_mapping = align(text,t_text)
                    
                    for label in attributes["annotations"]:
                        if label.start != char_mapping[label.start]:
                            label.start = char_mapping[label.start]
                            label_text = re.sub(rgx, r" \1 ", label.text)
                            label_text = re.sub("\s{2,}"," ",label_text)
                            label.end = label.start + len(label_text)
                    
                    text = t_text
                    
                doc = Document(pmid,text,attributes=attributes)
                self._docs[pmid] = doc
    
    def __getitem__(self,key):
        return self._docs[key]
    
    def _load(self, filename):
        for pmid in self._docs:
            yield self._docs[pmid]


def load_corpus(parser,entity_type="Disease",split_chars=[],overwrite=True):
    '''Load CDR Disease Corpus
    '''
    # init cache directory and parsers
    cache_dir = "{}/data/CDR.Corpus.v010516/cache/".format(os.path.dirname(__file__))
    if overwrite:
        filelist = glob.glob("{}/*.pkl".format(cache_dir))
        for fn in filelist:
            os.remove(fn)
        
    doc_parser = CdrParser(entity_type=entity_type,split_chars=split_chars)
    text_parser = PickleSerializedParser(parser,rootdir=cache_dir)
    
    # create cross-validation set information
    attributes = {"sets":{"testing":[],"training":[],"development":[]}}
    for pmid in doc_parser._docs:
        setname = doc_parser._docs[pmid].attributes["set"]
        attributes["sets"][setname]+= [pmid]
      
    return Corpus(doc_parser,text_parser,attributes)

    
