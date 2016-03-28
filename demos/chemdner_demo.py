# -*- coding: utf-8 -*-
import sys
import umls
from ddlite import *
from datasets import *
import codecs
from lexicons.matchers import DistributionalSimilarityMatcher

def de_corenlp(words):
    repl = dict([('-LRB-','('), ('-RRB-',')'), ('-LCB-','{'), ('-RCB-','}'), ('-LSB-','['),('-RSB-',']')])
    return [repl[w] if w in repl else w for w in words]

def get_mention_text(candidates):
    mentions = [de_corenlp([e.words[i] for i in e.idxs]) for e in candidates]
    return [" ".join(m) for m in mentions]

# ChemDNER Corpus v1.0
parser = SentenceParser()
corpus = ChemdnerCorpus('../datasets/chemdner_corpus/', parser=parser, cache_path="/tmp/")

pmids = [pmid for pmid in corpus.cv["training"].keys()[:1000]]
documents = {pmid:corpus[pmid]["sentences"] for pmid in pmids}
sentences = reduce(lambda x,y:x+y, documents.values())
print("Loaded %s training documents" % len(documents))

# load gold annotation tags
annotations = [corpus.annotations[pmid] for pmid in pmids if pmid in corpus.annotations]
annotations = reduce(lambda x,y:x+y, annotations)
annotations = [a.text for a in annotations]

regex_fnames = ["../datasets/regex/chemdner/patterns.txt"]

# dictionaries from tmChem
dict_fnames = ["../datasets/dictionaries/chemdner/mention_chemical.txt",
              "../datasets/dictionaries/chemdner/chebi.txt",
              "../datasets/dictionaries/chemdner/addition.txt"]

chemicals = []
for fname in dict_fnames:
    chemicals += [line.split("\t")[0] for line in open(fname,"rU").readlines()]

regexes = []
for fname in regex_fnames:
    regexes += [line.strip() for line in open(fname,"rU").readlines()] 

# build UMLS dictionary of substances (rather than query DB)
dfile = "../datasets/dictionaries/umls/substance-sab-all.txt"
if os.path.exists(dfile):
    d = {term.strip():1 for term in open(dfile,"rU").readlines()}
else:
    meta = umls.Metathesaurus()
    norm = umls.MetaNorm(function=lambda x:x.lower())
    d = meta.dictionary("Substance")
    d = map(norm.normalize,d)
    print("Found %d distinct terms" % len(d))
    with codecs.open(dfile,"w","utf-8") as f:
        for term in d:
            if term.strip() != "":
                try:
                    f.write(term)
                    f.write("\n")
                except:
                    print term
                    
chemicals += d.keys()

extr1 = DictionaryMatch('C', chemicals, ignore_case=True)
extr2 = RegexMatch('C',regexes[0], ignore_case=True)
extr3 = RegexMatch('C',regexes[2], ignore_case=False)


# slow -- also need to compute better embeddings
#embeddings = "/Users/fries/Desktop/chemdner_embeddings/embeddings/words.d128.w10.m0.i10.bin"
#extr4 = DistributionalSimilarityMatcher('C', embeddings, chemicals, 
#                                        knn=10, match_threshold=0.3, ignore_case=False)

matcher = MultiMatcher(extr3)


n,N = 0.0, 0.0
cand_n = 0
missed = []
for pmid in documents:
    sentences = documents[pmid]
    candidates = [m for m in Entities(sentences,matcher)]
    
    if pmid not in corpus.annotations:
        continue
    
    #print [m.text for m in corpus.annotations[pmid]]
    mentions = get_mention_text(candidates)
    
    annotations = [m.text for m in corpus.annotations[pmid]]
    counter = len(annotations)
    
    for m in mentions:
        if m in annotations:
            annotations.remove(m)
  
    n += counter - len(annotations)
    N += counter
    missed += annotations
    cand_n += len(candidates)
    
    for sent in sentences:
        sent = " ".join(sent.words)
        if "β-funaltrexamine" in sent:
            print sent
    
    
    if mentions:
        for m in  mentions:
            print m

missed = {term:missed.count(term) for term in missed}

regex = re.compile("^[αβΓγΔδεϝζηΘθικΛλμνΞξοΠπρΣστυΦφχΨψΩω]+[-]")
for term in missed:
    if regex.match(term):
        print "*",term
#    print term #, missed[term]
  

print n, N, len(missed)
print "%.3f" % (n/N)
print "candidates: %d" % cand_n
