from __future__ import print_function
import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import itertools
import numpy as np

#from ddlite import *
from ddlite_candidates import Candidates
from ddlite_candidates import Ngrams,Ngram
from ddlite_matchers import DictionaryMatch,Union,Concat,RegexMatchSpan

from ddbiolib.datasets import ncbi_disease
from versioning import CandidateVersioner
from ontologies.umls import UmlsNoiseAwareDict
from ontologies.ctd import load_ctd_dictionary
from ontologies.bioportal import load_bioportal_csv_dictionary

def clean_dictionary(dictionary ,stopwords, ignore_case=True):
    '''Remove stopwords'''
    rm = []
    for term in dictionary:
        t = term.lower() if ignore_case else term
        if t in stopwords:
            rm += [term]
    for t in rm:
        del dictionary[t]

def get_stopwords():
    dictfiles = ["../data/dicts/diseases/cell_molecular_dysfunction.txt",
                 "../data/dicts/diseases/umls_geographic_areas.txt",
                 "../data/dicts/diseases/stopwords.txt"]
    stopwords = {}
    for fname in dictfiles:
        d = [line.strip().split("\t")[0].lower() for line in open(fname).readlines()]
        d = [t for t in d if len(t) > 1 and t]
        stopwords.update(dict.fromkeys(d))
    return stopwords




common_disease_acronyms = ["AAPC", "AAS", "ABCD syndrome", "ACC", "ACS", "ACTH deficiency", "AD", "AD", "ADD",
                           "ADD-RT", "ADEM", "ADHD", "AF", "AGS", "AHC", "AIDS", "AIP", "ALA DD", "ALI", "ALS",
                           "AMD", "AOS", "APA", "APS", "ARBD", "ARD", "ARDS", "Acute respiratory distress syndrome",
                           "ARND", "AS", "ASD", "ASDs", "A-T", "AVMs", "B-NHL", "BBS", "BEB", "BD", "BEH", "BFIC", "BH", "BMD", "BPD",
                           "BPH", "BS", "BSE", "BSS", "BV", "CACH", "CAD", "CADSIL", "CAPD", "CCD", "CCHF", "CCHS",
                           "CCM", "CDG", "CDGS", "CEP", "CES", "CESD", "CF", "CFIDS", "CFS", "CGBD", "CHD", "CHF", "CHS"
                           "CIDP", "CIPA", "CJD", "CLD", "COFS", "COPD", "CP", "CP/CPPS", "CPDD", "CPM", "CPPS", "CRF",
                           "CRKP", "CRPS", "CSA", "CSD", "CVD", "DAS", "DBA", "DBMD", "DD", "DEF", "DF", "DH",
                           "DHF", "DiG", "DLB", "DM", "DMD", "DP", "DRSP disease", "DS", "DSPS", "DTs", "DVD",
                           "DVT", "ED", "EDS", "EEE", "EHK", "EMH", "EMR", "ENS", "EPM", "EPP", "ESRD", "ESS", "EVA"
                           "FAE", "FASDs", "FFI", "FMA", "FMD", "FMF", "FMS", "FNDI", "FSP", "FTD", "FVS", "FXS", 
                           "GAD", "GAN", "GAS disease", "GBS", "GBS disease", "GCE", "GERD", "GI", "GIB", "GN",
                           "GRMD", "GSS disease", "GT/LD", "GVHD", "GWD", "HAS", "HBL", "HCP", "HD", "HDL2", "HEELP syndrome",
                           "HFA", "HFMD", "HFRS", "HI", "HiB disease", "HMSN Type III", "HMS", "HOH", "HTN",
                           "HPRT deficiency", "HPS", "HPV Infection", "HSP", "IBD", "IBIDS syndrome", "IBM",
                           "IBS", "IBS", "IC/PBS", "ICF syndrome", "IDMS", "IHA", "IED", "IFAP syndrome", "INAD", "IP",
                           "IRD", "IS", "ITP", "JAS", "JE", "JHD", "JRA", "JT", "KS", "KSS", "KTW Syndrome",
                           "LCM", "LEMS", "LFA", "LGV", "LKS", "LNS", "LP", "MAC", "MBD", "MCS", "MD",
                           "MDD", "MDR TB", "MEF", "MHP", "MID", "MJD", "ML", "MLD", "MMA", "MMR", "MMRV", "MND", "MOH", "MPD",
                           "MPS I", "MPS II", "MPS III", "MPS IV", "MPS VI", "MPS VII", "MR/DD", "MS", "MSA",
                           "MSDD", "NAS", "NBIA", "NCL", "NF1", "NF2", "NKH", "NLD", "NMDs", "NMO", "NMS", "NP",
                           "NPC1", "NPH", "NTD", "NTDs", "OA", "OCD", "ODD", "OMA", "ON", "OPC", "OPCA", "OSA",
                           "PBC", "PBD", "PCOS", "PCT", "PDD", "PDD-NOS", "PDD/NOS", "PKAN", "PLMD", "PLS",
                           "PMD", "PML", "PMS", "POTS", "PPMA", "PPS", "PSC", "PSP", "PVL", "PW", "Q fever", "RA",
                           "RAD", "RIND", "RLF", "RLS", "RMDs", "ROP", "RS", "RSD", "RTI", "SARS", "SB", "SBS", "SC",
                           "SIDS", "SIS", "SLE", "SM", "SMA", "SMEI", "SMS", "SOD", "SPS", "SSPE", "STEMI",
                           "STD", "SUNCT", "SWS", "TAC", "TB", "TBI", "TCD", "TCS", "TEF", "TIA", "TMH", "TMJ/TMD", "TMR",
                           "TN", "TOS", "TS", "TS", "TSC", "TSEs", "TSP", "TTH", "TTP", "UCPPS", "UDA", "UTIs", "UC",
                           "URI", "VCFS", "vCJD", "VD", "VHF", "VP", "VSD", "VVC", "VWM disease",
                           "WAGR syndrome", "WD", "WEE", "WFS", "WS", "XLT", "XDR TB", "XLDCM", "XLSA", "XP", "YSS", "YVS", 
                           "ZBLS", "SCA1", "SCA2", "C1D", "C3D", "C4D", "C5D", "C6D", "C7D", "CCALD", "CL/P",
                           "SJS type 2"]


def clean_dictionary(d,stopwords,ignore_case=True):
    '''Remove some stopwords'''
    rm = []
    for term in d:
        t = term.lower() if ignore_case else term
        if t in stopwords:
            rm += [term]
            
    for t in rm:
        del d[t]

def get_stopwords():
    
    dictfile = "dicts/cell_molecular_dysfunction.txt"
    stopwords = dict.fromkeys([line.strip().split("\t")[0].lower() for line in open(dictfile).readlines()])
    #stopwords = {}
    dictfile = "dicts/umls_geographic_areas.txt"
    terms = [line.strip().split("\t")[0].lower() for line in open(dictfile).readlines()]
    stopwords.update(dict.fromkeys(terms))
    
    dictfile = "dicts/stopwords.txt"
    terms = [line.strip().split("\t")[0].lower() for line in open(dictfile).readlines()]
    stopwords.update(dict.fromkeys(terms))
    
    stopwords[""] = 1
    stopwords["a"] = 1
    
    return stopwords


def get_gold_labels(corpus,doc_ids=None):
    '''Generate gold labels for the provided corpus. Note: requires an "annotations"
    attribute'''
    labels = []
    for doc in corpus:
        if not doc_ids or doc.doc_id not in doc_ids:
            continue
         
        sent_offsets = [s._asdict()["char_offsets"][0] for s in doc.sentences]
        for label in doc.attributes["annotations"]:
            sidx = -1
            for i in range(len(sent_offsets) - 1):
                if label.start >= sent_offsets[i] and label.end - 1 < sent_offsets[i+1]:
                    sidx = i
                    break
            if label.start >= sent_offsets[-1]:
                sidx = len(sent_offsets) - 1
                
            # label crosses multiple sentence boundaries
            if sidx == -1:
                print("WARNING sentence boundary error",file=sys.stderr)
            
            metadata = {"mention_type":label.mention_type}
            labels += [Ngram(label.start, label.end - 1, doc.sentences[sidx], metadata=metadata)]
            if labels[-1].get_span() == "":
                print(labels[-1])
                print(label)
                print(doc.sentences[sidx])
                print("--------")
            
    return labels

# --------------------------------------------
# Load/Parse Corpus
# --------------------------------------------
corpus = ncbi_disease.load_corpus()

# --------------------------------------------
# Load Dictionaries / Ontologies
# --------------------------------------------
# UMLS semantic types that map to diseases or disorders
positive = ["Acquired Abnormality",
            "Anatomical Abnormality",
            "Congenital Abnormality",
            "Disease or Syndrome",
            "Experimental Model of Disease",
            "Finding",
            "Injury or Poisoning",
            "Mental or Behavioral Dysfunction",
            "Neoplastic Process",
            "Pathologic Function",
            "Sign or Symptom"]

negative = ["Physiologic Function","Molecular Function","Genetic Function",
            "Cell Function","Organ or Tissue Function","Organism Function", "Food",
            "Mental Process","Molecular Sequence","Nucleotide Sequence", "Animal",
            "Carbohydrate Sequence","Amino Acid Sequence","Body Substance",
            "Cell","Gene or Genome","Cell Component","Functional Concept",
            "Spatial Concept","Molecular Biology Research Technique",
            "Laboratory or Test Result","Laboratory or Test Result",
            "Animal","Therapeutic or Preventive Procedure","Bacterium","Phenomenon or Process",
            "Quantitative Concept","Temporal Concept","Natural Phenomenon or Process",
            "Body Part, Organ, or Organ Component","Body Location or Region",
            "Body Space or Junction", "Pathologic Function"]

umls_terms = UmlsNoiseAwareDict(positive=positive, name="terms", ignore_case=False)
umls_abbrv = UmlsNoiseAwareDict(positive=positive, name="abbrvs", ignore_case=False)
#umls_stopwords = UmlsNoiseAwareDict(negative=negative, name="terms", ignore_case=True)

diseases = umls_terms.dictionary() # create stand alone dictionaries
#abbrvs = umls_abbrv.dictionary()
#stopwords = umls_stopwords.dictionary()

#diseases = load_disease_dictionary()
abbrvs = load_acronym_dictionary()
abbrvs.update(dict.fromkeys(common_disease_acronyms))

# Load various other disease ontologies
ordo = load_bioportal_csv_dictionary("dicts/ordo.csv")
doid = load_bioportal_csv_dictionary("dicts/DOID.csv")
ctd = load_ctd_dictionary("dicts/CTD_diseases.tsv") # CTD's MEDIC disease vocabulary

diseases.update(ordo)
diseases.update(doid)
diseases.update(ctd)
clean_dictionary(diseases,get_stopwords())

print("DICTIONARY Disease Terms: {}".format(len(diseases)))
print("DICTIONARY Abbreviation/Acronym Terms: {}".format(len(abbrvs)))

# --------------------------------------------
# Match Candidates
# --------------------------------------------
# Define a candidate space
ngrams = Ngrams(n_max=8)

longest_match = True

dict_diseases = DictionaryMatch(label='disease', d=diseases, 
                            ignore_case=True, longest_match=longest_match)
dict_abbrvs = DictionaryMatch(label='disease_acronyms', d=abbrvs, 
                            ignore_case=False, longest_match=longest_match)


stem_forms = DictionaryMatch(label='disease_stems', d=dict.fromkeys(diseases.keys() + abbrvs.keys()),
                             ignore_case=False, longest_match=longest_match)

# prefix concatenatior matchers
suffixes = DictionaryMatch(label="prefixes", d=['deficiency', 'deficient', 'deficienty', 'syndrome'],
                           ignore_case=True, longest_match=longest_match)
disease_deficiency = Concat(stem_forms, suffixes)

# disease types 
digits = map(unicode,range(1,10))
types = DictionaryMatch(label="prefixes", d=['type', 'class', 'stage', 'factor'],
                        ignore_case=True, longest_match=longest_match)
type_nums = DictionaryMatch(label="prefixes", d=['i', 'ii', 'iii', 'vi', 'v', 'vi', '1a', 'iid', 'a', 'b', 'c', 'd'] + digits,
                            ignore_case=True, longest_match=longest_match)
disease_types_right = Concat(stem_forms, Concat(types,type_nums))
disease_types_left = Concat(Concat(types,type_nums),stem_forms)

# deficiency of
prefixes = DictionaryMatch(label="prefixes",d=['deficiency of',"inherited"],
                           ignore_case=True, longest_match=longest_match)
deficiency_of = Concat(prefixes,stem_forms)

# sex_linked
gene_linked = DictionaryMatch(label="x-linked", d=["x-linked","x linked","x linked recessive","semidominant",
                                                   "hereditary",
                                                   "recessive","x-linked recessive", "x-linked dominant",
                                                   "dominant",'autosomal recessive',"autosomal dominant",
                                                   "autossomal recessive"],
                            ignore_case=True, longest_match=longest_match)
gene_linked = Concat(gene_linked,stem_forms)

cancers = RegexMatchSpan(label="cancers",rgx="(^[A-Za-z]+ (and|and/or|or) [A-Za-z]+ cancer[s]*$)|(^[A-Za-z]+[\/-][A-Za-z]+ cancer[s]*$)")
deficient = RegexMatchSpan(label="deficient",rgx="^[A-Za-z0-9]+[-]deficient$")


matcher = Union(dict_diseases, dict_abbrvs, disease_deficiency, deficient, cancers,
                disease_types_left, disease_types_right, deficiency_of, gene_linked)

holdouts = ["training","development"]#,"testing"]
for setname in holdouts:
    
    doc_ids = corpus.attributes["sets"][setname]
    cs = Candidates(ngrams, matcher, corpus.get_sentences(doc_ids))
    candidates = cs.get_candidates()
    gold = frozenset(get_gold_labels(corpus,doc_ids))
    
    print("----------------------------------")
    print(setname)
    print("----------------------------------")
    print("%d PubMed abstracts" % len(doc_ids))
    print("%d Disease gold entities" % len(gold))
    print("%d Candidates" % len(candidates)) 
    
    cs.gold_stats(gold)
    
    fn = []
    for c in gold:
        if c not in candidates:
            fn += [c.get_span()]
    
    fn = {term:fn.count(term) for term in set(fn)}
    for item in sorted(fn.items(),key=lambda x:x[1],reverse=0):
        print(item)
    
    #for c in candidates:
    #    print(c)
    '''
    for label in gold:
        if label not in candidates:
            print(label.get_span(), label.get_span().lower() in diseases)
    '''
sys.exit()


