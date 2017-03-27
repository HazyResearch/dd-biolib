import os
import re
import sys
import glob
import codecs
import tarfile
import subprocess
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


def annotate_doc(annotations, doc, uid):
    '''
    Create document sequence and labels. i2b2 offsets
    are of the form <LINE>:<TOKEN> where LINE offsets begin
    at 1 and TOKEN offsets begin at 0 (ugh).
    Use IOB format (inside, outside, beginning)
    Example medication mention
    B-m, I-m, O
    '''
    labels = [['O' for _ in line] for line in doc]

    for mention in annotations:
        for item in mention:

            entity_label = item[0]

            # if there is a mention, determine the text span
            if item[-1]:

                for offset in item[-1]:
                    begin, end = offset

                    if begin[0] != end[0]:
                        span_n = len(doc[begin[0] - 1][begin[1]:])
                        span_n += len(doc[end[0] - 1][:end[1] + 1])

                        # generate IOB labels
                        span = ["I-%s" % entity_label] * span_n
                        span[0] = "B-%s" % entity_label

                        span_n = len(doc[begin[0] - 1][begin[1]:])
                        labels[begin[0] - 1][begin[1]:] = span[0:span_n]
                        labels[end[0] - 1][:end[1] + 1] = span[span_n:]

                    else:
                        # generate IOB labels
                        span = ["I-%s" % entity_label] * (end[1] - begin[1] + 1)
                        span[0] = "B-%s" % entity_label
                        labels[begin[0] - 1][begin[1]:end[1] + 1] = span

    return labels



def annotate_doc_2(annotations, sents, uid):

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
                    print>>sys.stderr,"skipping discontinuous spans", entity
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
                    #labels += [(mention,char_start,char_end)]

            except:
                print >>sys.stderr,"ERROR parsing", entity


    # merge sentences using heuristic rule
    merge_sent_idxs.update(repair_i2b2_sentence_boundaries(sents))
    sents = merge_sentences(sents, merge_sent_idxs)

    m_text = "\n".join([" ".join(s) for s in sents])

    # validate labels match new offsets
    for lbl in labels:
        mention,i,j = lbl.text, lbl.start, lbl.end
        if mention.lower() != m_text[i:j].lower().replace("\n"," "):
            print mention, "VS", m_text[i:j]
            print lbl

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


    def __init__(self, inputpath=None, entity_type="drug", split_chars=[], use_unlabeled=False):
        super(i2b2MedicationParser, self).__init__(inputpath, "utf-8")

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

    def __expand_tokens(self, sentences, tags):
        '''
        Several heuristics for dealing with noisy tokens in the i2b2
        medication challenge data set. This includes
        '''
        updated = False
        for i in range(len(sentences)):
            s, t = [], []

            for idx, word in enumerate(sentences[i]):

                if len(word) == 1 or self.freq_regex.match(word):
                    s += [sentences[i][idx]]
                    t += [tags[i][idx]]
                    continue

                # if word.count("/") > 1 and not date_regex.match(word) and \
                #  not telephone_regex.match(word) and re.sub("[0-9./]","",word).strip() != "" and \
                #  re.match("([A-Za-z0-9]+[/])+",word):
                #    print word


                if re.match("^([*]+[A-Za-z0-9]+$)|([A-Za-z0-9]+?[*]+)$", word):

                    subseq = [x for x in re.split("([*]+)", word) if x]

                    if tags[i][idx].split("-") == ["O"]:
                        s += subseq
                        t += ['O', 'O']

                    else:
                        prefix = tags[i][idx].split("-")[0]
                        etype = tags[i][idx].split("-")[-1]
                        s += subseq
                        t += ['%s-%s' % (prefix, etype), 'I-%s' % (etype)]

                    updated = 1

                # split training puncutation
                elif (word[-1] in ["."] and word not in self.abbrv) or word[-1] in [",", ":", ";", "(", ")", "/"]:
                    s += [sentences[i][idx][0:-1], word[-1]]
                    t += [tags[i][idx], 'O']
                    updated = 1

                # split words consisting of concatenated tokens
                elif re.search("^[a-zA-Z]{4,}[/.;:][a-zA-Z]{4,}$", word) or \
                        re.search("^[a-zA-Z0-9]{2,}[=>][a-zA-Z0-9%.]{2,}$", word):

                    # subseq = re.split("([/.;:=])",word)
                    # split on first matched split token
                    sidx = [word.index(ch) for ch in re.findall("([/.;:=>])", word)][0]
                    subseq = [word[0:sidx], word[sidx], word[sidx + 1:]]

                    if tags[i][idx].split("-") == ["O"]:
                        s += subseq
                        t += ['O', 'O', 'O']
                    else:
                        prefix = tags[i][idx].split("-")[0]
                        etype = tags[i][idx].split("-")[-1]
                        s += subseq
                        t += ['%s-%s' % (prefix, etype), 'I-%s' % (etype), 'I-%s' % (etype)]

                    updated = 1

                # leave word as-is
                else:
                    s += [sentences[i][idx]]
                    t += [tags[i][idx]]

            sentences[i] = s
            tags[i] = t

        return updated

    def __repair(self, sentences, tags):
        '''
        HACK function to fix sentence boundaries and word tokenization issues
        in original corpus release. This is just a bunch of rules and observations
        specific to the i2b2 corpus. If we don't fix sentences, then BIO
        tagging breaks in several instances.
        '''
        # 1: Expand tokens
        while self.__expand_tokens(sentences, tags):
            pass

        # 2: Create new sentence boundaries by merging sentences
        dangling = [",", "Dr.", 'as', 'of', 'and', 'at'] + prepositions.keys()
        sentence_fragments = ["Please see", "The"]

        m_sentences, m_tags = [], []
        curr_sentence, curr_tags = [], []
        dangler = False

        for i in range(len(sentences)):

            if not sentences[i]:
                continue

            # ends if a preposition or other known dangling word
            if dangler:
                curr_sentence += [sentences[i]]
                curr_tags += [tags[i]]

            elif sentences[i][0][0].islower() and curr_sentence:
                curr_sentence += [sentences[i]]
                curr_tags += [tags[i]]

            elif curr_sentence:
                curr_sentence = reduce(lambda x, y: x + y, curr_sentence)
                curr_tags = reduce(lambda x, y: x + y, curr_tags)

                m_sentences += [curr_sentence]
                m_tags += [curr_tags]

                curr_sentence, curr_tags = [], []
                curr_sentence += [sentences[i]]
                curr_tags += [tags[i]]

            else:
                curr_sentence = [sentences[i]]
                curr_tags = [tags[i]]

            dangler = sentences[i][-1] in dangling

        if curr_sentence:
            m_sentences += [reduce(lambda x, y: x + y, curr_sentence)]
            m_tags += [reduce(lambda x, y: x + y, curr_tags)]

        #:3 split sentences
        dangling = False
        f_sentences, f_tags = [], []

        for i in range(len(m_sentences)):

            splits = []
            for j in range(len(m_sentences[i]) - 1):
                if m_sentences[i][j] == "." and m_sentences[i][j + 1][0].isupper():
                    splits += [j + 1]
            splits += [len(m_sentences[i])]

            curr = 0

            for idx in splits:
                sentence = m_sentences[i][curr:idx]
                tags = m_tags[i][curr:idx]

                if dangling:
                    f_sentences[-1] += sentence
                    f_tags[-1] += tags
                    dangling = False

                else:
                    f_sentences += [sentence]
                    f_tags += [tags]

                if " ".join(sentence).strip() in sentence_fragments:
                    dangling = True

                curr = idx

        return f_sentences, f_tags

    def _tags2offsets(self, sents, tags):

        # create annotations
        labels = []
        shift = 0
        char_offsets = []
        for i in range(len(sents)):
            s = zip(sents[i],tags[i])
            offsets = [shift]
            for chunk in [" ".join(sents[i][0:j]) for j in range(1,len(sents[i])+1)]:
                offsets.append(len(chunk)+1+shift)

            char_offsets.append(offsets[:-1])
            shift = offsets[-1]

            annotations = []
            curr = []
            for w in zip(sents[i],tags[i],offsets):
                term,tag,char_start = w
                if tag[0] == 'B':
                    if curr:
                        annotations.append(curr)
                        curr = []
                    curr.append(w)
                elif tag[0] == 'I':
                    curr.append(w)
                elif curr:
                    annotations.append(curr)
                    curr = []

            for ann in annotations:
                term,tag,span = zip(*ann)
                mention = " ".join(term)
                entity_type = tag[0].split("-")[-1]
                char_start, char_end = span[0],span[-1]+len(term[-1])


                label = Annotation(entity_type, char_start, char_end, mention)
                labels += [label]

        return labels



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
            self.labels[uid], self.documents[uid] = annotate_doc_2(self.annotations[uid], self.documents[uid], uid)

        # repair sentence boundary errors
        for uid in self.documents:
            if uid not in self.labels:
                merge_sent_idxs = repair_i2b2_sentence_boundaries(self.documents[uid])
                self.documents[uid] = merge_sentences(self.documents[uid], merge_sent_idxs)

        for uid in self.documents:
            attributes = {}
            text = "\n".join([" ".join(s) for s in self.documents[uid]])

            if uid not in self.labels:
                attributes["set"] = "training"
                attributes["annotations"] = []
            else:
                attributes["set"] = "testing"
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


