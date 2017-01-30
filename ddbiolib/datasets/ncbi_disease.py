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


def align(a, b):
    j = 0
    offsets = []
    for i in range(0, len(a)):
        if a[i] in [" "]:
            continue

        matched = False
        while not matched and j < len(b):
            if a[i] == b[j]:
                offsets += [(i, j, a[i], b[j])]
                matched = True
            j += 1

    token_idx, doc_idx, token_ch, doc_ch = zip(*offsets)
    return offsets, dict(zip(token_idx, doc_idx))

class NcbiDiseaseParser(DocParser):
    '''
    The NCBI disease corpus is fully annotated at the mention and concept level 
    to serve as a research resource for the biomedical natural language processing 
    community.     -- from http://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/
                    
        793 PubMed abstracts
        6,892 disease mentions
        790 unique disease concepts
    
    '''
    def __init__(self, inputpath=None, split_chars=[], use_unlabeled=False):
        super(NcbiDiseaseParser, self).__init__(inputpath, "utf-8")
        self.split_chars = split_chars

        if not inputpath:
            self.inputpath = "{}/data/ncbi_disease_corpus/".format(os.path.dirname(__file__))
        else:
            self.inputpath = inputpath
        print self.inputpath
        self._docs = {}
        self._download()
        self._preload(use_unlabeled)
        
    def _download(self):
        '''If corpus files aren't available, automatically download them'''
        url = "http://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/"
        filelist = ["NCBItrainset_corpus.zip","NCBItestset_corpus.zip","NCBIdevelopset_corpus.zip"]
        
        for fname in filelist:
            outfname = "{}{}".format(self.inputpath,fname)
            if os.path.exists(outfname):
                continue
            
            print("Downloading NCBI Disease Corpus dataset [{}]...".format(os.path.basename(outfname)))
            download(url+fname,outfname)
            cwd = os.getcwd()
            os.chdir(self.inputpath)
            subprocess.call(["unzip", outfname])
            os.chdir(cwd)
            
    def _preload(self, use_unlabeled=False):
        '''Load corpus into memory'''
        Annotation = namedtuple('Annotation', ['text_type','start','end','text','mention_type'])
        
        # holdout set definitions
        cvdefs = {"NCBIdevelopset_corpus.txt":"development",
                  "NCBItestset_corpus.txt":"testing",
                  "NCBItrainset_corpus.txt":"training",
                  "pubmed.random.100000.txt": "random-100k"
                  }

        if not use_unlabeled:
            del cvdefs["pubmed.random.100000.txt"]

        filelist = glob.glob("%s/*.txt" % self.inputpath)

        for fname in filelist:
            name = fname.split("/")[-1]
            if name not in cvdefs:
                continue
            setname = cvdefs[name]
            documents = []
            with codecs.open(fname, "rU", self.encoding) as f:
                doc = []
                for line in f:
                    row = line.strip()
                    if not row and doc:
                        documents += [doc]
                        doc = []
                    elif row:
                        row = row.split("|") if (len(row.split("|")) > 1 and
                                                 row.split("|")[1] in ["t", "a"]) else row.split("\t")
                        doc += [row]
                if doc:
                    documents += [doc]

            for doc in documents:
                pmid, title, abstract = doc[0][0], doc[0][2], doc[1][2]
                text = "%s %s" % (title, abstract)

                attributes = {"set": setname, "title": title, "abstract": abstract}
                attributes["annotations"] = []

                # load annotation tuples
                for row in doc[2:]:

                    # relation
                    # ----------------------------
                    if len(row) <= 4:
                        pmid, rela, m1, m2 = row
                        continue

                    # entity
                    # ----------------------------
                    if len(row) == 6:
                        pmid, start, end, mention, mention_type, duid = row
                        norm_names = []
                    elif len(row) == 7:
                        pmid, start, end, mention, mention_type, duid, norm_names = row
                    duid = duid.split("|")

                    start, end = int(start), int(end)
                    text_type = "T" if end <= len(title) else "A"

                    label = Annotation(text_type, start, end, mention, mention_type)
                    attributes["annotations"] += [label]

                #
                # Force tokenization on certain characters BEFORE parsing
                #
                if self.split_chars:
                    rgx = "([{}])".format("".join(self.split_chars))
                    t_text = re.sub(rgx, r" \1 ", text)
                    t_text = re.sub("\s{2,}", " ", t_text)
                    text += " " * (len(t_text) - len(text))
                    _, char_mapping = align(text, t_text)

                    for label in attributes["annotations"]:
                        if label.start != char_mapping[label.start]:
                            label.start = char_mapping[label.start]
                            label_text = re.sub(rgx, r" \1 ", label.text)
                            label_text = re.sub("\s{2,}", " ", label_text)
                            label.end = label.start + len(label_text)

                    text = t_text

                doc = Document(pmid, text, attributes=attributes)
                self._docs[pmid] = doc

        '''
        filelist = glob.glob("%s/*.txt" % self.inputpath)
        print len(filelist)
        for fname in filelist:
            name = fname.split("/")[-1]
            if name not in cvdefs:
                continue
            setname = cvdefs[name]

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
                documents += [doc]
      
            for doc in documents:
                pmid,title,abstract = doc[0][0],doc[0][2],doc[1][2]
                text = "%s %s" % (title, abstract)
                attributes = {"set":setname,"title":title,"abstract":abstract}            
                attributes["annotations"] = []
                
                # load annotation tuples
                for row in doc[2:]:
                    pmid, start, end, mention, mention_type, duid = row
                    start,end = int(start),int(end)
                    text_type = "T" if end <= len(title) else "A" 
                    label = Annotation(text_type, start, end, mention, mention_type)
                    attributes["annotations"] += [label]

                # warning if PMID is already loaded
                if pmid in self._docs:
                    print >> sys.stderr, "WARNING: Duplicate PMID {} found".format(pmid)
                    
                doc = Document(pmid,text,attributes=attributes)
                self._docs[pmid] = doc
        '''

    def __getitem__(self,key):
        return self._docs[key]
    
    def _load(self, filename):
        for pmid in self._docs:
            yield self._docs[pmid]


def load_corpus(parser, entity_type="Disease", split_chars=[], overwrite=False, use_unlabeled=False):

    # init cache directory and parsers
    cache_dir = "{}/data/ncbi_disease_corpus/cache/".format(os.path.dirname(__file__))
    doc_parser = NcbiDiseaseParser(split_chars=split_chars, use_unlabeled=use_unlabeled)
    text_parser = PickleSerializedParser(parser, rootdir=cache_dir)
    
    # create cross-validation set information
    attributes = {"sets":{"testing":[],"training":[],"development":[],
                          "random-100k": [], "query-100k": []}}
    for pmid in doc_parser._docs:
        setname = doc_parser._docs[pmid].attributes["set"]
        attributes["sets"][setname] += [pmid]

    print "Loaded NCBI Disease corpus"
    return Corpus(doc_parser,text_parser,attributes)



