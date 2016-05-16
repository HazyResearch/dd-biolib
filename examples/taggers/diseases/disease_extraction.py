import bz2
import sys
import csv
import re
import numpy as np
import itertools
import cPickle
import ddlite
from ddlite import SentenceParser,Entities
from ddlite import Union, DictionaryMatch, RegexNgramMatch
from utils import unescape_penn_treebank
from datasets import NcbiDiseaseCorpus

ROOT = "/Users/fries/dd-bio-examples/"
INDIR = "/Users/fries/Desktop/dnorm/"
#OUTDIR = "/users/fries/desktop/dnorm/"
OUTDIR = "/Users/fries/Desktop/dnorm/candidates/v5/"

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
    #dictfile = "dicts/umls_disorders.bz2"
    #dictfile = "dicts/umls_disorders_snomed_msh_mth.bz2"
    dictfile = "dicts/umls_disorders_v2.bz2"
    diseases = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(dictfile, 'rb').readlines()}
    diseases = {word:1 for word in diseases if not word.isupper()}

    # Orphanet Rare Disease Ontology
    ordo = load_bioportal_csv_dictionary("dicts/ordo.csv")
    ordo = {word:1 for word in ordo if not word.isupper()}
    diseases.update(ordo)
    
    # Human Disease Ontology 
    doid = load_bioportal_csv_dictionary("dicts/DOID.csv")
    doid = {word:1 for word in doid if not word.isupper()}
    diseases.update(doid)
      
    # ------------------------------------------------------------
    # remove cell dysfunction terms
    dictfile = "dicts/cell_molecular_dysfunction.txt"
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    diseases = {word:1 for word in diseases if word not in terms} 
    
    dictfile = "dicts/umls_geographic_areas.txt"
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    diseases = {word:1 for word in diseases if word not in terms}
    # ------------------------------------------------------------
    
    # NCBI training set vocabulary
    dictfile = "dicts/ncbi_training_diseases.txt"
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    terms = {word:1 for word in terms if not word.isupper()}
    diseases.update(terms)
    
    # remove stopwords
    dictfile = "dicts/stopwords.txt".format(rootdir)
    stopwords = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    diseases = {word:1 for word in diseases if word.lower() not in stopwords}  
    
    return diseases

def load_acronym_dictionary(rootdir):    
    
    #dictfile = "dicts/umls_disorders.bz2"
    #dictfile = "dicts/umls_disorders_snomed_msh_mth.bz2" # candidate recall: 74.59% (587/787)
    dictfile = "dicts/umls_disorders_v2.bz2"
    diseases = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(dictfile, 'rb').readlines()}
    diseases = {word:1 for word in diseases if word.isupper()}
    
    # Orphanet Rare Disease Ontology
    ordo = load_bioportal_csv_dictionary("dicts/ordo.csv")
    ordo = {word:1 for word in ordo if word.isupper()}
    diseases.update(ordo)
    
    # Human Disease Ontology 
    doid = load_bioportal_csv_dictionary("dicts/DOID.csv")
    doid = {word:1 for word in doid if word.isupper()}
    diseases.update(doid)
    
    dictfile = "dicts/ncbi_training_diseases.txt".format(rootdir)
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    terms = {word:1 for word in terms if word.isupper()}
    diseases.update(terms)
    
    # filter by char length
    diseases = {word:1 for word in diseases if len(word) > 1}
    
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
num_gold_entities = sum([len(s) for s in list(itertools.chain.from_iterable(gold_entities))])
num_tokens = sum([len(sent.words) for sent in list(itertools.chain.from_iterable(documents))])
print("%d PubMed abstracts" % len(documents))
print("%d Disease gold entities" % num_gold_entities)
print("%d tokens" % num_tokens)

# --------------------------------------------
# Match Candidates
# --------------------------------------------

diseases = load_disease_dictionary(ROOT)
acronyms = load_acronym_dictionary(ROOT)

matcher_d = DictionaryMatch(label='D', dictionary=diseases, ignore_case=True)

#matcher_tags = TagMatch(tag="JJ")
#concat_matcher = Concat(matcher_tags,matcher_d)

matcher_a = DictionaryMatch(label='D', dictionary=acronyms, ignore_case=False)
matcher = Union(matcher_a, matcher_d)

#pattern = re.compile("((JJ|VBN)\s)+(NN[SP]*\s*)+")
#pattern = re.compile("((NN[SP]*|JJ)\s*){2,}")
pattern = re.compile("((NN[SP]*|JJ|IN DT)\s*){2,}") #of the/ in the

matcher_tags = RegexNgramMatch(label="D",match_attrib="poses",regex_pattern=pattern,ignore_case=False)

matcher = Union(matcher_a, matcher_d, matcher_tags)
#matcher = matcher_tags

gold_labels = []
scores = {"num_candidates":0, "num_cand_tokens":0}


# DEBUG
'''
sentences = [corpus[doc_id]["sentences"] for doc_id in ['9472666']]
sentences = list(itertools.chain.from_iterable(sentences))
candidates = Entities(sentences, matcher)
for c in candidates:
    print c.mention(), [c.poses[i] for i in c.idxs]

for sentence in corpus['9472666']["sentences"]:
    print sentence.words, sentence.poses

pred = [1] * len(candidates)
tp,fp,fn = corpus.classification_errors(candidates, pred)
for item in fn:
    doc_id,sent_id,idxs,char_span,txt = item
    print [corpus[doc_id]['sentences'][sent_id].words[i] for i in idxs]
    print [corpus[doc_id]['sentences'][sent_id].poses[i] for i in idxs]
    print
    
sys.exit()
'''

for cv_set in holdouts:
    sentences = [corpus[doc_id]["sentences"] for doc_id in corpus.cv[cv_set]]
    sentences = list(itertools.chain.from_iterable(sentences))
    
    candidates = Entities(sentences, matcher)
    gold_labels = corpus.gold_labels(candidates)
    
    for c in candidates:
        print c.mention(), [c.poses[i] for i in c.idxs]
    
    pred = [1] * len(candidates)
    scores[cv_set] = corpus.score(candidates, pred)
    scores["num_candidates"] += len(candidates)
    scores["num_cand_tokens"] += sum([len(c.idxs) for c in candidates])
    
    
    tp,fp,fn = corpus.classification_errors(candidates, pred)
    
    for item in fn:
        doc_id,sent_id,idxs,char_span,txt = item
        print [corpus[doc_id]['sentences'][sent_id].words[i] for i in idxs]
        print [corpus[doc_id]['sentences'][sent_id].poses[i] for i in idxs]
        print
    np.save("{}/{}-ncbi-diseases-gold.npy".format(OUTDIR,cv_set), gold_labels)
    candidates.dump_candidates("{}/{}-ncbi-candidates.pkl".format(OUTDIR,cv_set))


# candidate recall
print("Found %d candidate entities (%.2f%% of all tokens)" % (scores["num_candidates"],
                                                              scores["num_cand_tokens"]/float(num_tokens)*100)) 
for cv_set in ["training","development","testing"]:
    print("[{0}] candidate recall: {1:0.2f}% ({2}/{3})".format(cv_set.upper(),scores[cv_set]["recall"]*100,
                                                             scores[cv_set]["tp"], 
                                                             scores[cv_set]["tp"]+ scores[cv_set]["fn"]))



