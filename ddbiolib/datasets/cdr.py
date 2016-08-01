import os
import sys
import glob
import codecs
import subprocess
from collections import namedtuple
from ..utils import download
from ..corpora import Corpus,Document,DocParser
from ..parsers import CoreNlpParser,PickleSerializedParser

class CdrParser(DocParser):
    '''
        The CDR disease corpus 
                             -- f                    
        1500 PubMed abstracts
        X disease mentions
        X chemical mentions
    '''
    def __init__(self, inputpath=None, entity_type="Disease"):
        super(CdrParser, self).__init__(inputpath, "utf-8")
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
        Annotation = namedtuple('Annotation', ['text_type','start','end','text','mention_type'])
        
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

                doc = Document(pmid,text,attributes=attributes)
                self._docs[pmid] = doc
    
    def __getitem__(self,key):
        return self._docs[key]
    
    def _load(self, filename):
        for pmid in self._docs:
            yield self._docs[pmid]


def load_corpus(entity_type="Disease",parser=CoreNlpParser()):
    '''Load CDR Disease Corpus
    '''
    # init cache directory and parsers
    cache_dir = "{}/data/CDR.Corpus.v010516/cache/".format(os.path.dirname(__file__))
    doc_parser = CdrParser(entity_type=entity_type)
    text_parser = PickleSerializedParser(parser,rootdir=cache_dir)
    
    # create cross-validation set information
    attributes = {"sets":{"testing":[],"training":[],"development":[]}}
    for pmid in doc_parser._docs:
        setname = doc_parser._docs[pmid].attributes["set"]
        attributes["sets"][setname]+= [pmid]
      
    return Corpus(doc_parser,text_parser,attributes)


