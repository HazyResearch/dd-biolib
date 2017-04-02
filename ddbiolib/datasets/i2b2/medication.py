import os
import re
import sys
import glob
import codecs
import tarfile
import subprocess
import numpy as np
from collections import namedtuple,defaultdict
from ddbiolib.utils import download
from ddbiolib.corpora import Corpus, Document, DocParser
from ddbiolib.parsers import PickleSerializedParser

# regular expressions for normalizing common entities
date_regex = re.compile("\d{1,2}/\d{1,2}/\d{1,4}")
telephone_regex = re.compile("\d{3}-\d{3}-\d{4}|\(\d{3}\) \d{3}[ -]+\d{4}")

prepositions = ['aboard', 'about', 'above', 'across', 'after', 'against',
                'along', 'alongside', 'amid', 'among', 'around', 'at', 'atop',
                'barring', 'before', 'behind', 'below', 'beneath', 'beside',
                'besides', 'between', 'beyond', 'but', 'by', 'concerning',
                'considering', 'despite', 'down', 'during', 'except', 'for',
                'from', 'in', 'inside', 'into', 'like', 'near', 'nearby',
                'of', 'off', 'on', 'onto', 'opposite', 'out', 'outside',
                'over', 'past', 'per', 'regarding', 'round', 'since',
                'through', 'throughout', 'till', 'to', 'towards', 'under', "than",
                'underneath', 'until', 'unto', 'up', 'upon', 'with', 'within',
                'without', "final"]

prepositions = {x: 1 for x in prepositions}


def unescape_chars(m):
    m = m.replace("&gt;", ">")
    m = m.replace("&lt;", "<")
    m = m.replace("&amp;", "&")
    return m

def discharge_summary_parser(f, normalize):
    '''
    i2b2 2009 discharge summaries are split on line
    and tokenized by whitespace. Line and term offsets
    are used by the annotation format.
    '''
    doc = []
    for line in f:
        #line = line.replace("&gt;", ">")
        #line = line.replace("&lt;", "<")
        #line = line.replace("&amp;", "&")

        line = unescape_chars(line)

        #tokens = line.split() #line.strip().split()
        tokens = re.split('\s', line)
        #tokens = re.split(r'(\s+)', line)

        doc += [tokens]

    return doc


def annotation_parser(f, rm_tags=[]):
    '''i2b2 annotation format'''
    # m="cisplatin." 26:5 26:5||do="nm"||mo="nm"||f="nm"||du="nm"||r="nm"||ln="narrative"
    annotations = []

    for line in f:
        row = line.strip().split("||")
        mention = []

        for item in row:
            m = re.search('(m|do|mo|f|du|r|ln)="(.+)"', item)

            entity_type = m.group(1)
            text_span = m.group(2)

            if entity_type in rm_tags:
                continue

            offsets = item.replace(m.group(0), "").strip()
            if offsets:
                offsets = offsets.split(",")
                for i in range(len(offsets)):
                    offsets[i] = map(lambda x: map(int, x.split(":")), offsets[i].split())

            mention += [(entity_type, text_span, offsets)]
        annotations += [mention]

    return annotations


def annotate_doc(annotations, sents, uid):

    skipped = []
    shift = 0
    char_offsets = []
    labels = []
    for i in range(len(sents)):

        # remove null string tokens, bug preserve offsets for annotations
        sents[i] = sents[i] if sents[i][-1] != "" else sents[i][:-1]
        if sents[i] and len(sents[i]) > 2:
            tmp = [sents[i][0]] + [s for s in sents[i][1:-1] if s] + [sents[i][-1]]
            if tmp != sents[i]:
                sents[i] = tmp

        offsets = [shift]
        for chunk in [" ".join(sents[i][0:j]) for j in range(1, len(sents[i]) + 1)]:
            offsets.append(len(chunk) + 1 + shift)

        char_offsets.append(offsets[:-1])
        shift = offsets[-1]

    text = "\n".join([" ".join(s) for s in sents])
    merge_sent_idxs = {}

    for anno in annotations:
        for entity in anno:
            entity_type,mention,span = entity
            mention = unescape_chars(mention)

            try:
                # HACK - just use medications for now
                if entity_type not in ["m"]:
                    continue

                if entity_type in ["ln"] or entity[1] == "nm":
                    continue

                if len(span) != 1:
                    skipped += [entity]
                    continue

                for subspan in span:
                    # setup span offsets
                    start_sent,i = subspan[0]
                    end_sent,j = subspan[1]
                    start_sent -= 1
                    end_sent -= 1
                    char_start = char_offsets[start_sent][i]

                    # fix conflict between annotation mention and document span
                    char_end = char_start + len(mention)

                    if end_sent != start_sent:
                        merge_sent_idxs[end_sent] = 1

                    span_text = text[char_start:char_end].replace("\n", " ")
                    span_text = span_text.lower()
                    mention = mention.lower()

                    # fix mis-aligned mentions
                    if span_text != mention:
                        while span_text[0] != mention[0]:
                            char_start += 1
                            char_end += 1
                            span_text = text[char_start:char_end].replace("\n", " ").lower()

                    if span_text != mention:
                        print "ERROR", uid
                        print "ADD", end_sent-start_sent
                        print "MENTION",mention
                        print "SPAN",span_text
                        print "SENT",sents[start_sent]
                        print 'char start',char_start
                        print "--->",[text[char_start:char_start+len(mention)]]
                        print mention, subspan
                        print "===="

                    if mention[-1] == ".":
                        mention = mention[:-1]
                        char_end -= 1

                    labels += [Annotation(entity_type, char_start, char_end, mention)]


            except:
                print >>sys.stderr,"ERROR parsing", entity


    # merge sentences using heuristic rule
    merge_sent_idxs.update(repair_i2b2_sentence_boundaries(sents))
    sents = merge_sentences(sents, merge_sent_idxs)

    m_text = "\n".join([" ".join(s) for s in sents])

    # validate labels match new offsets
    for lbl in labels:
        mention,i,j = lbl.text, lbl.start, lbl.end
        if mention.lower() != m_text[i:j].lower().replace("\n"," ") or (mention==""):
            print mention, "VS", m_text[i:j]
            print lbl


    if len(skipped) > 0:
        print>> sys.stderr, "skipping {} discontinuous spans".format(len(skipped))

    return labels, sents


def repair_i2b2_sentence_boundaries(sents):
    idxs = {}
    dangling = [",", "Dr.", 'as', 'of', 'and', 'at'] + prepositions.keys()
    for i in range(0,len(sents)):
        if sents[i][-1] in dangling:
            idxs[i+1] = 1
    return idxs

def merge_sentences(sents,merge_sent_idxs):
    '''

    :param sents:
    :param idxs:
    :return:
    '''
    for i in sorted(merge_sent_idxs,reverse=1):
        m_sents = sents[0:i]
        m_sents[-1] += sents[i]
        m_sents.extend(sents[i+1:])
        sents = m_sents

    return sents

class Annotation(object):

    def __init__(self, mention_type, start, end, text):
        self.mention_type = mention_type
        self.start = start
        self.end = end
        self.text = text

    def __str__(self):
        return "Annotation({}, start={}, end={}, text={})".format(self.mention_type,
                                                                  self.start, self.end,
                                                                  self.text)


class i2b2MedicationParser(DocParser):


    def __init__(self, inputpath=None, entity_type="drug", split_chars=[],
                 use_unlabeled=False, verbose=False):
        super(i2b2MedicationParser, self).__init__(inputpath, "utf-8")

        self.verbose = verbose
        self.freq_regex = re.compile("q\.\d+h\.")
        self.qty_regex = re.compile("\d,\d+")

        self.normalize = False
        type_map = {"drug":"m"}
        self.rm_tags = []
        self.entity_type = "m"

        infile = "{}/data/medication/abbreviations.txt".format(os.path.dirname(__file__))
        self.abbrv = {t.strip() for t in open(infile,"rU").readlines()}

        self.documents = {}
        self.annotations = {}
        self.labels = {}

        self.split_chars = split_chars
        if not inputpath:
            self.inputpath = "{}/data/medication/".format(os.path.dirname(__file__))
        else:
            self.inputpath = inputpath
        self._docs = {}

        self._preload(entity_type, use_unlabeled)


    def _preload(self, et, use_unlabeled=False):

        length = 0
        docfiles = glob.glob("{}/documents/*".format(self.inputpath))
        labelfiles = glob.glob("{}/annotations/*".format(self.inputpath))

        docfiles = [x for x in docfiles if ".py" not in x]
        labelfiles = [x for x in labelfiles if ".py" not in x]

        # match annotations with documents
        labelmap = {fname.split("/")[-1].split(".")[0]: fname for fname in labelfiles}
        docmap = {fname.split("/")[-1]: fname for fname in docfiles}

        # Load annotations
        for uid in labelmap:
            with codecs.open(labelmap[uid], "rU", self.encoding) as f:
                self.annotations[uid] = annotation_parser(f, self.rm_tags)

        # Load documents / normalize terms
        for uid in docmap:
            with codecs.open(docmap[uid], "rU", self.encoding) as f:
                self.documents[uid] = discharge_summary_parser(f, normalize=self.normalize)

        # convert annotations to doc char offsets
        for idx, uid in enumerate(self.annotations):
            self.labels[uid], self.documents[uid] = annotate_doc(self.annotations[uid], self.documents[uid], uid)

        # repair sentence boundary errors
        for uid in self.documents:
            if uid not in self.labels:
                merge_sent_idxs = repair_i2b2_sentence_boundaries(self.documents[uid])
                self.documents[uid] = merge_sentences(self.documents[uid], merge_sent_idxs)

        # define folds (use labeled data for dev/test only)
        np.random.seed(12345)
        uids = self.labels.keys()
        np.random.shuffle(uids)
        fold_defs = {"development":uids[0:125],"testing":uids[125:]}
        #print len(fold_defs["testing"])
        #print len(fold_defs["development"])
        dev_fold = dict.fromkeys(uids[0:125])
        #test_fold = dict.fromkeys(uids[125:])

        for uid in self.documents:
            attributes = {}
            text = "\n".join([" ".join(s) for s in self.documents[uid]])

            if uid not in self.labels:
                attributes["set"] = "training"
                attributes["annotations"] = []
            else:
                attributes["set"] = "testing" if uid in dev_fold else "development"
                attributes["annotations"] = self.labels[uid]

            self._docs[uid] = Document(uid, text, attributes=attributes)


    def __getitem__(self, key):
        return self._docs[key]

    def _load(self, filename):
        for pmid in self._docs:
            yield self._docs[pmid]



def load_corpus(parser, entity_type="protein", use_unlabeled=False):
    '''

    :param parser:
    :param entity_type:
    :param use_unlabeled:
    :return:
    '''

    # init cache directory and parsers
    cache_dir = "{}/data/medication/cache/".format(os.path.dirname(__file__))

    doc_parser = i2b2MedicationParser(entity_type=entity_type, use_unlabeled=use_unlabeled)
    text_parser = PickleSerializedParser(parser, rootdir=cache_dir)

    # create cross-validation set information
    attributes = {"sets": {"testing": [], "training": [], "development": [],
                           "random-100k": []}}

    for pmid in doc_parser._docs:
        setname = doc_parser._docs[pmid].attributes["set"]
        attributes["sets"][setname] += [pmid]

    return Corpus(doc_parser, text_parser, attributes)


