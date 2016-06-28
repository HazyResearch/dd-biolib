import bz2
import sys
import csv
import re
import codecs
import numpy as np
import itertools
import cPickle
import ddlite
from ddlite import SentenceParser,Entities
from ddlite import Union, DictionaryMatch, RegexNgramMatch, CandidateExtractor
from utils import unescape_penn_treebank
from datasets import NcbiDiseaseCorpus

class PrefixDictionaryMatcher(RegexNgramMatch):
    
    def init(self):
        super(PrefixDictionaryMatcher, self).init()
        self.dictionary = self.opts['dictionary']
        self.ignore_case       = self.opts.get('ignore_case', True)
        
    def _apply(self, s, idxs=None):
        candidates = [c for c in super(PrefixDictionaryMatcher, self)._apply(s,idxs)]
        for idxs,label in candidates:
            matched = False
            
            words = unescape_penn_treebank([s.words[i] for i in idxs])
            matched = reduce(lambda x,y:x or y,[t in self.dictionary for t in words])
            '''
            for i in range(len(idxs)):
                for j in range(i+1,len(idxs)):
                    phrase = " ".join(unescape_penn_treebank(s.words[idxs[i]:idxs[j]+1]))
                    phrase = phrase.lower() if self.ignore_case else phrase
                    print phrase
                    if phrase in self.dictionary:
                        matched = True
                        #break
            '''
            if matched:
                yield idxs, label


class HackDictionaryMatcher(RegexNgramMatch):
    
    def init(self):
        super(HackDictionaryMatcher, self).init()
        self.dictionary = self.opts['dictionary']
        self.ignore_case       = self.opts.get('ignore_case', True)


    def _apply(self, s, idxs=None):
        candidates = [c for c in super(PrefixDictionaryMatcher, self)._apply(s,idxs)]
        for idxs,label in candidates:
            matched = False
            
            words = unescape_penn_treebank([s.words[i] for i in idxs])
            matched = reduce(lambda x,y:x or y,[t in self.dictionary for t in words])
            s = " ".join(words)
            if matched and (" in the " in s or " of the " in s):
                yield idxs, label
    
    '''
    def _apply(self, s, idxs=None):
        
        candidates = [c for c in super(HackDictionaryMatcher, self)._apply(s,idxs)]
        for idxs,label in candidates:
            matched = False
            
            yield idxs, label
            
            words = unescape_penn_treebank([s.words[i] for i in idxs])
            matched = reduce(lambda x,y:x or y,[t in self.dictionary for t in words])
            s = " ".join(words)
            
            if re.search(" (of|in) the ", s) != None and matched:
                yield idxs, label
    '''




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





ROOT = "/Users/fries/dd-bio-examples/"
INDIR = "/Users/fries/Desktop/ncbi/"
OUTDIR = "/Users/fries/Desktop/ncbi/candidates/"

# --------------------------------------------
# Load/Parse Corpus
# --------------------------------------------

cache = "{}/cache/".format(INDIR)
infile = "{}/corpora/".format(INDIR)
holdouts = ["training","development","testing"]

parser = SentenceParser()
corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)

for doc_id in ['10923035']:# corpus.cv["training"]:
    doc = corpus[doc_id]
    print doc_id
    for sentence in doc["sentences"]:
        print sentence.parse
    print "--------"

sys.exit()

'''
d = create_corpus_dict(corpus,"development")
fname = "dicts/ncbi_development_diseases.txt"
with codecs.open(fname,"w",'utf-8') as f:
    f.write("\n".join(d.keys()))

d = create_corpus_dict(corpus,"testing")
fname = "dicts/ncbi_testing_diseases.txt"
with codecs.open(fname,"w",'utf-8') as f:
    f.write("\n".join(d.keys()))
sys.exit()
'''

oracle = create_corpus_dict(corpus,"development")
oracle.update(create_corpus_dict(corpus,"testing"))

#dev_set = list(itertools.chain.from_iterable([corpus.cv[setdef].keys() for setdef in holdouts]))
#documents, gold_entities = zip(*[(corpus[doc_id]["sentences"],corpus[doc_id]["tags"]) for doc_id in dev_set])

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

longest_match = True
matcher_d = DictionaryMatch(label='disease', dictionary=diseases, ignore_case=True, longest_match=longest_match)
matcher_a = DictionaryMatch(label='disease_acronyms', dictionary=acronyms, ignore_case=False, longest_match=longest_match)
matcher_oracle = DictionaryMatch(label='disease_oracle', dictionary=oracle, ignore_case=False, longest_match=longest_match)

pattern = re.compile("((NN[SP]*|JJ)\s*){2,}")  
disease_terms = diseases.keys()
disease_terms = {t:1 for t in disease_terms if len(t.split()) == 1}

matcher_jj = PrefixDictionaryMatcher(label="D",match_attrib="poses",
                                       dictionary=disease_terms, longest_match=longest_match,
                                       regex_pattern=pattern,ignore_case=False)



pattern = re.compile("((NN[SP]*|JJ)\s*){2,}")  
matcher_np = RegexNgramMatch(label="D",match_attrib="poses",
                             longest_match=longest_match,
                             regex_pattern=pattern,ignore_case=False)


matcher = Union(matcher_a, matcher_d, matcher_oracle)


gold_labels = []
scores = {"num_candidates":0, "num_cand_tokens":0,"class_balance":{}}

for cv_set in holdouts:
    scores["class_balance"][cv_set] = {}
    
    sentences = [corpus[doc_id]["sentences"] for doc_id in corpus.cv[cv_set]]
    sentences = list(itertools.chain.from_iterable(sentences))
    
    candidates = Entities(sentences, matcher)
    gold_labels = corpus.gold_labels(candidates)

    pred = [1] * len(candidates)
    scores[cv_set] = corpus.score(candidates, pred)
    scores["num_candidates"] += len(candidates)
    scores["num_cand_tokens"] += sum([len(c.idxs) for c in candidates])
    
    
    tp,fp,fn = corpus.classification_errors(candidates, pred)
    
    scores["class_balance"][cv_set]["T"] = len(tp)
    scores["class_balance"][cv_set]["F"] = len(candidates) - len(tp)
    
    for item in fn:
        doc_id,sent_id,idxs,char_span,txt = item
        print "FN"
        print [corpus[doc_id]['sentences'][sent_id].words[i] for i in idxs]
        print [corpus[doc_id]['sentences'][sent_id].poses[i] for i in idxs]
        print
    np.save("{}/{}-ncbi-diseases-gold.npy".format(OUTDIR,cv_set), gold_labels)
    candidates.dump_candidates("{}/{}-ncbi-candidates.pkl".format(OUTDIR,cv_set))
    

# candidate recall
print("Found %d candidate entities (%.2f%% of all tokens)" % (scores["num_candidates"],
                                                              scores["num_cand_tokens"]/float(num_tokens)*100)) 
for cv_set in ["training","development","testing"]:
    print "Positives:{} Negatives:{}".format(scores["class_balance"][cv_set]["T"],scores["class_balance"][cv_set]["F"])
    print("[{0}] candidate recall: {1:0.2f}% ({2}/{3})".format(cv_set.upper(),scores[cv_set]["recall"]*100,
                                                             scores[cv_set]["tp"], 
                                                             scores[cv_set]["tp"]+ scores[cv_set]["fn"]))



