import bz2
import itertools
from ddlite import *
from datasets import NcbiDiseaseCorpus

def load_dictionary():    
    # stopwords
    dictfile = "datasets/dictionaries/chemdner/stopwords.txt"
    stopwords = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    
    dictfile = "datasets/dictionaries/umls/umls_disease_syndrome.bz2"
    diseases = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(dictfile, 'rb').readlines()}
    diseases = {word:1 for word in diseases if word not in stopwords}
    
    return diseases

'''
parser = SentenceParser()
cache = "/Users/fries/Desktop/dnorm/cache/"
infile = "/Users/fries/Desktop/dnorm/disease_names/"
corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)

pmids = list(itertools.chain.from_iterable([corpus.cv[setdef].keys() for setdef in corpus.cv.keys()]))
print len(pmids)
docs = [(pmid,corpus[pmid]["sentences"]) for pmid in pmids] 
pmids,sentences = zip(*docs)
sentences = list(itertools.chain.from_iterable(sentences))

print "Loaded {} documents".format(len(docs))
print "       {} sentences".format(len(sentences))

diseases = load_dictionary()
matcher = DictionaryMatch(label='D', dictionary=diseases, ignore_case=True)

candidates = Entities(sentences, matcher)
candidates.dump_candidates("/Users/fries/Desktop/dnorm/all-ncbi-umls-disease-candidates.pkl")

print candidates.num_candidates()
sys.exit()
'''
#
# Corpus
#
cache = "/Users/fries/Desktop/dnorm/cache/"
infile = "/Users/fries/Desktop/dnorm/disease_names/"

parser = SentenceParser()
corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)

#dev_set = sorted(corpus.cv["evaluation"].keys())
dev_set = list(itertools.chain.from_iterable([corpus.cv[setdef].keys() for setdef in corpus.cv.keys()]))
documents, gold_entities = zip(*[(corpus[doc_id]["sentences"],corpus[doc_id]["tags"]) for doc_id in dev_set])

# summary statistics
gold_entity_n = sum([len(s) for s in list(itertools.chain.from_iterable(gold_entities))])
word_n = sum([len(sent.words) for sent in list(itertools.chain.from_iterable(documents))])
print("%d PubMed abstracts" % len(documents))
print("%d Disease gold entities" % gold_entity_n)
print("%d tokens" % word_n)

#
# Match Candidates
#
diseases = load_dictionary()
matcher = DictionaryMatch(label='D', dictionary=diseases, ignore_case=True)

#
# Candidate Recall
#
num_candidates = 0
candidate_gold_labels = []
tp, fn, gold = [],[],[]

# compute matched mention spans for each document
for sentences,labels in zip(documents, gold_entities):
    match_idx = {}
    matches = Entities(sentences, matcher)
    num_candidates += matches.num_candidates()
    
    # group candidates by sentence
    candidates = {}
    for i,m in enumerate(matches):
        text = [m.words[i] for i in m.idxs]
        c = (" ".join(text), (m.idxs[0], m.idxs[0] + len(text))) # (text, span)
        candidates[m.sent_id] = candidates.get(m.sent_id,[]) + [c]
        match_idx[c] = i
        
    # match to gold labels
    gold_labels = [0] * len(matches)
    for sent_id in range(len(sentences)):
        hits = [m for m in candidates[sent_id] if m in labels[sent_id]] if sent_id in candidates else []
        fn += [m for m in labels[sent_id] if m not in hits]
        tp += hits
        gold += labels[sent_id]
        # create gold labels for candidates
        for c in tp:
            gold_labels[match_idx[c]] = 1
        for c in fn:
            gold_labels[match_idx[c]] = 0
    
    candidate_gold_labels += gold_labels
    
print("Found %d candidate entities (%.2f%% of all tokens)" % (num_candidates, num_candidates/float(word_n)*100)) 
print("Candidate Recall: %.2f (%d/%d)" % (len(tp)/float(len(gold)), len(tp), len(gold)))
print("Candidate False Negative Rate (FNR) %.2f" % (1.0 - len(tp)/float(len(gold))))

candidate_gold_labels = np.ndarray(candidate_gold_labels)
candidate_gold_labels = 2 * candidate_gold_labels - 1
print candidate_gold_labels


# dump all candidates to a pickle file
#candidates = Entities(sentences, matcher)
#candidates.dump_candidates("candidates/chemnder-training-candidates.pkl")



sys.exit()








# candidate data
docs = [(pmid,corpus[pmid]["sentences"]) for pmid in corpus.cv["training"]]
#pmids,docs = zip(*docs)

# stopwords
dictfile = "datasets/dictionaries/chemdner/stopwords.txt"
stopwords = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]

dictfile = "datasets/dictionaries/umls/umls_disease_syndrome.bz2"
diseases = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(dictfile, 'rb').readlines()}
diseases = {word:1 for word in diseases if word not in stopwords}

# NCBI training vocab
#dictfile = "datasets/dictionaries/ncbi/ncbi_training_diseases.txt"
#ncbi_terms = {line.strip().split("\t")[0]:1 for line in open(dictfile).readlines()}
#diseases.update(ncbi_terms)

matcher = DictionaryMatch('D', diseases, ignore_case=True)

# dump candidates
candidate_set = []
recall = [0.0,0.0]

gold = []
wtf = []
for pmid,sentences in docs:
    #sentences = docs[pmid]
    matches = [m for m in Entities(sentences, matcher)]

    offsets = {}
    gold_labels = {idx:0 for idx in range(0,len(matches))}
    
    # bin candidates by sentence id
    candidates = {}
    for sent_id,s in enumerate(sentences):
        candidates[sent_id] = {}
        for i,m in enumerate(matches):
            
            offsets[m] = i
            
            if m.sent_id != s.sent_id:
                continue
            candidates[s.sent_id][m.idxs[0]] = candidates[s.sent_id].get(m.idxs[0],[]) + [m]
   
    for sent_id,entities in enumerate(corpus[pmid]["tags"]):
        
        if sent_id not in candidates:
            continue
        
        matched_candidates = []
        tp,fn = [],[]
        
        for text,span in entities:
            i,j = span
            if i in candidates[sent_id]:
                mentions = [ ([m.words[i] for i in m.idxs],m) for m in candidates[sent_id][span[0]]]
                mentions = sorted(mentions,key=lambda x:len(x[0]),reverse=1)[0]
                mspan = (mentions[1].idxs[0],mentions[1].idxs[0] + len(mentions[1].idxs))
                tp += [ (" ".join(mentions[0]), mspan ) ]
                matched_candidates += [mentions[1]]
        
        if entities:
            fn = [item for item in entities if item not in tp]

        recall[1] += len(entities)
        recall[0] += len(tp)
        
        local_tp = 0
        for idx in [offsets[m] for m in matched_candidates]:
            gold_labels[idx] = 1
            local_tp += 1
        '''
        if local_tp != len(tp):
            print local_tp, len(tp)
            print tp
            print entities
            
        wtf += [local_tp]
        '''
    gold += [gold_labels]

print recall
print sum(wtf)
# create mindtagger gold labels
v = []
for doc in gold:
    for i in sorted(doc):
        v += [doc[i]]


print len(gold)
print len(docs)
print sum(v)
print sum([sum(doc.values()) for doc in gold])
np.save(open("/users/fries/desktop/ncbi.training-umls-only.npy","w"),v)
print "saved gold labels"

#
# Dump ddite files
#

corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)
docs = {pmid:corpus[pmid]["sentences"] for pmid in corpus.cv["testing"]} 
pmids,sentences = zip(*docs)
sentences = list(itertools.chain.from_iterable(sentences))
matcher = DictionaryMatch('D', diseases, ignore_case=True)

candidates = Entities(sentences, matcher)
candidates.dump_candidates("/Users/fries/Desktop/dnorm/training-umls-only-pubmed-disease-candidates.pkl")


