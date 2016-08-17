import bz2
from ontologies.umls import UmlsNoiseAwareDict
from ontologies.ctd import load_ctd_dictionary
from ontologies.bioportal import load_bioportal_csv_dictionary
#from tools import load_disease_dictionary,load_acronym_dictionary


def search(term,dictionary):
    m = {}
    for sty in dictionary:
        for sab in dictionary[sty]:
            if term in dictionary[sty][sab]:
                m[sty] = 1
    
    return m.keys()
    

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

umls_terms = UmlsNoiseAwareDict(positive=positive, prefix="terms")
umls_abbrv = UmlsNoiseAwareDict(positive=positive, prefix="abbrvs", ignore_case=False)

diseases = umls_terms.dictionary() # create stand alone dictionaries
abbrvs = umls_abbrv.dictionary()


print len(diseases)


dictfile = "dicts/umls_disorders_v2.bz2"
disorders = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(dictfile, 'rb').readlines()}
#disorders = {word:1 for word in disorders if word.isupper()}
disorders = {word.lower():1 for word in disorders if not word.isupper()}

print len(disorders)


for term in diseases:
    if term not in disorders:
        print term, search(term,umls_terms._dictionary)
        
