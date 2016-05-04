import bz2
import sys
import csv
import numpy as np
import itertools
from ddlite import SentenceParser,DictionaryMatch,Entities,Union
from utils import unescape_penn_treebank
from datasets import NcbiDiseaseCorpus

ROOT = "/Users/fries/dd-bio-examples/"
INDIR = "/Users/fries/Desktop/dnorm/"
OUTDIR = "/users/fries/desktop/dnorm/"


def load_bioportal_csv_dictionary(filename):
    '''BioPortal Ontologies
    http://bioportal.bioontology.org/'''
    
    reader = csv.reader(open(filename,"rU"),delimiter=',', quotechar='"')
    d = [line for line in reader]
    
    dictionary = {}
    for line in d[1:]:
        row = dict(zip(d[0],line))
        dictionary[row["Preferred Label"]] = 1
        dictionary.update({t:1 for t in row["Synonyms"].split("|")})
        
    return dictionary
    

def load_disease_dictionary(rootdir):  
      
    # UMLS SemGroup Disorders
    dictfile = "dicts/umls_disorders.bz2".format(rootdir)
    diseases = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(dictfile, 'rb').readlines()}
    diseases = {word:1 for word in diseases if not word.isupper()}
    
    # Orphanet Rare Disease Ontology
    ordo = load_bioportal_csv_dictionary("dicts/ordo.csv")
    ordo = {word:1 for word in ordo if not word.isupper()}
    diseases.update(ordo)
    
    # Human Disease Ontology 
    doid = load_bioportal_csv_dictionary("dicts/DOID.csv")
    doid = {word:1 for word in ordo if not word.isupper()}
    diseases.update(doid)
    
    # NCBI training set vocabulary
    dictfile = "dicts/ncbi_training_diseases.txt".format(rootdir)
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    terms = {word:1 for word in terms if not word.isupper()}
    diseases.update(terms)
    
    # remove stopwords
    dictfile = "dicts/stopwords.txt".format(rootdir)
    stopwords = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    diseases = {word:1 for word in diseases if word not in stopwords}
    
    return diseases

def load_acronym_dictionary(rootdir):    
    
    dictfile = "dicts/umls_disorders.bz2".format(rootdir)
    diseases = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(dictfile, 'rb').readlines()}
    diseases = {word:1 for word in diseases if word.isupper()}
    
    # Orphanet Rare Disease Ontology
    ordo = load_bioportal_csv_dictionary("dicts/ordo.csv")
    ordo = {word:1 for word in ordo if word.isupper()}
    diseases.update(ordo)
    
    # Human Disease Ontology 
    doid = load_bioportal_csv_dictionary("dicts/DOID.csv")
    doid = {word:1 for word in ordo if word.isupper()}
    diseases.update(doid)
    
    dictfile = "dicts/ncbi_training_diseases.txt".format(rootdir)
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    terms = {word:1 for word in terms if not word.isupper()}
    diseases.update(terms)
    
    return diseases

def create_corpus_dict(corpus, setdef="training"):
    '''Create dictionary using annotated corpus data'''
    dev_set = list(itertools.chain.from_iterable([corpus.cv[setdef].keys() for setdef in [setdef]]))
    documents = [(doc_id,corpus[doc_id]["sentences"],corpus[doc_id]["tags"]) for doc_id in dev_set]
    
    print len(dev_set),len(corpus.documents)
    
    d = {}
    for pmid,doc,labels in documents:
        for i in range(0,len(doc)):
            for tag in labels[i]:
                mention = doc[i].words[tag[-1][0]:tag[-1][1]]
                v1 = "".join(unescape_penn_treebank(mention))
                v2 = tag[0].replace(" ","")
                if v1 != v2:
                    # problem with tokenization
                    #print " ".join(unescape_penn_treebank(mention)), tag
                    pass
                else:
                    d[" ".join(mention)] = 1                    
    return d


# --------------------------------------------
# Load/Parse Corpus
# --------------------------------------------

cache = "{}/cache3/".format(INDIR)
infile = "{}/disease_names/".format(INDIR)
holdouts = ["training","development","testing"]

parser = SentenceParser()
corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)

dev_set = list(itertools.chain.from_iterable([corpus.cv[setdef].keys() for setdef in holdouts]))
documents, gold_entities = zip(*[(corpus[doc_id]["sentences"],corpus[doc_id]["tags"]) for doc_id in dev_set])

# summary statistics
gold_entity_n = sum([len(s) for s in list(itertools.chain.from_iterable(gold_entities))])
word_n = sum([len(sent.words) for sent in list(itertools.chain.from_iterable(documents))])
print("%d PubMed abstracts" % len(documents))
print("%d Disease gold entities" % gold_entity_n)
print("%d tokens" % word_n)

# --------------------------------------------
# Match Candidates
# --------------------------------------------

diseases = load_disease_dictionary(ROOT)
acronyms = load_acronym_dictionary(ROOT)

matcher_d = DictionaryMatch(label='D', dictionary=diseases, ignore_case=True)
matcher_a = DictionaryMatch(label='D', dictionary=acronyms, ignore_case=False)
matcher = Union(matcher_a, matcher_d)

candidates = []
gold_labels = []

for cv_set in holdouts:
    sentences = [corpus[doc_id]["sentences"] for doc_id in corpus.cv[cv_set]]
    sentences = list(itertools.chain.from_iterable(sentences))
    
    matches = Entities(sentences, matcher)
    gold_labels += corpus.gold_labels(matches)
    candidates += [matches]
    
    pred = [1] * len(matches)
    scores = corpus.score(matches,pred)
    print cv_set, scores
    
# dump candidates and gold labels
all_candidates = Entities([])
all_candidates._candidates = list(itertools.chain.from_iterable(candidates))
all_candidates.dump_candidates("{}/all-ncbi-candidates.pkl".format(OUTDIR))
np.save("{}/all-ncbi-candidates-gold.npy".format(OUTDIR),gold_labels)

# candidate recall
pred = [1] * len(all_candidates)
scores = corpus.score(all_candidates,pred)
print scores
print "candidate holdout splits", [len(c) for c in candidates]

#print("Found %d candidate entities (%.2f%% of all tokens)" % (num_candidates, num_candidates/float(word_n)*100)) 
#print("Candidate Recall: %.2f (%d/%d)" % (len(tp)/float(len(gold)), len(tp), len(gold)))
#print("Candidate False Negative Rate (FNR) %.2f" % (1.0 - len(tp)/float(len(gold))))








sys.exit()
#
# Candidate Recall
#
num_candidates = 0
candidate_doc_index = []
candidate_gold_labels = []
tp, fn, gold = [],[],[]

splits = {}
for pmid,sentences,labels in zip(dev_set,documents, gold_entities):
    
    holdout = "training"
    if pmid in corpus.cv["development"]:
        holdout = "development"
    elif pmid in corpus.cv["testing"]:
        holdout = "testing"
    
    matches = Entities(sentences, matcher)
    num_candidates += matches.num_candidates()
    
    candidate_gold_labels += corpus.gold_labels(matches)
    print candidate_gold_labels[0:100]
    splits[holdout] = len(candidate_gold_labels)
    


'''
# compute matched mention spans for each document
for pmid,sentences,labels in zip(dev_set,documents, gold_entities):
    
    holdout = "training"
    if pmid in corpus.cv["development"]:
        holdout = "development"
    elif pmid in corpus.cv["testing"]:
        holdout = "testing"
    
    match_idx = {i:{} for i in range(len(sentences))}
    matches = Entities(sentences, matcher)
    num_candidates += matches.num_candidates()
    
    # group candidates by sentence
    candidates = {}
    for idx,m in enumerate(matches):
        text = [m.words[i] for i in m.idxs]
        c = (" ".join(text), (m.idxs[0], m.idxs[0] + len(text))) 
        candidates[m.sent_id] = candidates.get(m.sent_id,[]) + [c]
        match_idx[m.sent_id][c] = idx
 
    # match to gold labels
    gold_labels = [0] * len(matches)
    for sent_id in range(len(sentences)):
        hits = [m for m in candidates[sent_id] if m in labels[sent_id]] if sent_id in candidates else []
        fn += [m for m in labels[sent_id] if m not in hits]
        tp += hits
        gold += labels[sent_id]
        # create gold labels for candidates
        for c in hits:
            gold_labels[match_idx[sent_id][c]] = 1
            
    candidate_gold_labels += gold_labels
    
    splits[holdout] = len(candidate_gold_labels)
    
    
    if pmid == "1248000":
        for lbl in labels:
            print lbl
        print "-------------"
        for m in matches:
            
            words = [m.words[i] for i in m.idxs]
            char_idxs = [m.token_idxs[i] for i in m.idxs]
            print char_idxs
            print "words:", " ".join(words)
            print "span:", char_idxs[0], char_idxs[-1] + len(words[-1])
        print "-------------"
'''

print("Found %d candidate entities (%.2f%% of all tokens)" % (num_candidates, num_candidates/float(word_n)*100)) 
print("Candidate Recall: %.2f (%d/%d)" % (len(tp)/float(len(gold)), len(tp), len(gold)))
print("Candidate False Negative Rate (FNR) %.2f" % (1.0 - len(tp)/float(len(gold))))
print(splits.items())

candidate_gold_labels = np.asarray(candidate_gold_labels)
candidate_gold_labels = 2 * candidate_gold_labels - 1
np.save("{}/all-ncbi-candidates-gold.npy".format(OUTDIR),candidate_gold_labels)

# dump all candidates to a pickle file
sentences = list(itertools.chain.from_iterable(documents))
candidates = Entities(sentences, matcher)
candidates.dump_candidates("{}/all-ncbi-candidates.pkl".format(OUTDIR))


