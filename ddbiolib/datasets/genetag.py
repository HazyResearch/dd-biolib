import os
import re
import sys
import glob
import codecs
import zipfile
import subprocess
from collections import namedtuple
from ..utils import download
from ..corpora import Corpus, Document, DocParser
from ..parsers import PickleSerializedParser





class Annotation(object):
    def __init__(self, text_type, start, end, text, mention_type, uids=[]):
        self.text_type = text_type
        self.start = start
        self.end = end
        self.text = text
        self.mention_type = mention_type
        self.uids = uids

    def __str__(self):
        return "Annotation(start={}, end={}, text={})".format(self.start, self.end, self.text)


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


class GeneTagParser(DocParser):


    def __init__(self, inputpath=None, entity_type="GENE", split_chars=[], use_unlabeled=False):
        super(GeneTagParser, self).__init__(inputpath, "utf-8")
        self.split_chars = split_chars
        if not inputpath:
            self.inputpath = "{}/data/GeneTag/".format(os.path.dirname(__file__))
        else:
            self.inputpath = inputpath
        self._docs = {}

        if not os.path.exists(self.inputpath):
            os.makedirs(self.inputpath)
            self._download()
        self._preload(entity_type, use_unlabeled)

    def _download(self):

        url = "https://excellmedia.dl.sourceforge.net/project/bioc/"
        filelist = ["GeneTag.zip"]
        os.chdir(self.inputpath)

        for fname in filelist:
            outfname = "{}{}".format(self.inputpath, fname)
            if os.path.exists(outfname):
                continue

            print("Downloading GeneTag Corpus [{}]...".format(os.path.basename(outfname)))
            download(url + fname, outfname)

            zipf = zipfile.ZipFile(outfname, 'r')
            zipf.extractall()
            zipf.close()

            print "EXTRACTED"

    def _preload(self, et, use_unlabeled=False):

        cvdefs = {"genetag5000_BioC.xml": "testing",
                  "genetag15000_BioC.xml": "training",
                  "pubmed.random.100000.txt": "random-100k"
                  }

        if not use_unlabeled:
            del cvdefs["pubmed.random.100000.txt"]

        documents = {}
        folds = {}
        for filename in cvdefs:

            with codecs.open(filename, "rU", self.encoding) as fp:
                doc = {}
                for line in fp:
                    mid = re.search("^###MEDLINE:([0-9]+)$",line)
                    if mid:
                        if doc:
                            doc[doc.keys()[0]] = [s for s in doc.values()[0] if s]
                            documents.update(doc)
                        doc = {mid.group(1):[]}
                        folds[mid.group(1)] = cvdefs[filename]
                    else:
                        line = line.strip()
                        if line:
                            doc[doc.keys()[0]][-1].append(line.split())
                        else:
                            doc[doc.keys()[0]].append([])

        for mid in documents:

            doc = [zip(*s) for s in documents[mid]]
            sents,tags = [s[0] for s in doc], [s[1] for s in doc]
            text = " ".join([" ".join(s) for s in sents])

            attributes = {"set": folds[mid], "abstract": text}
            attributes["annotations"] = []


            #     if mention_type != et:
            #         continue
            #     label = Annotation(text_type, start, end, mention, mention_type, duid)
            #     attributes["annotations"] += [label]
            #
            doc = Document(mid, text, attributes=attributes)
            self._docs[mid] = doc




        '''
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

                    if mention_type != et:
                        continue
                    label = Annotation(text_type, start, end, mention, mention_type, duid)
                    attributes["annotations"] += [label]


                doc = Document(pmid, text, attributes=attributes)
                self._docs[pmid] = doc
        '''

    def __getitem__(self, key):
        return self._docs[key]

    def _load(self, filename):
        for pmid in self._docs:
            yield self._docs[pmid]


def load_corpus(parser, use_unlabeled=False):

    # init cache directory and parsers
    cache_dir = "{}/data/GeneTag/cache/".format(os.path.dirname(__file__))

    doc_parser = GeneTagParser(use_unlabeled=use_unlabeled)
    text_parser = PickleSerializedParser(parser, rootdir=cache_dir)

    # create cross-validation set information
    attributes = {"sets": {"testing": [], "training": [], "development": [],
                           "random-100k": [], "query-100k": []}}

    for pmid in doc_parser._docs:
        setname = doc_parser._docs[pmid].attributes["set"]
        attributes["sets"][setname] += [pmid]

    return Corpus(doc_parser, text_parser, attributes)


