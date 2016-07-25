import bz2
from ontologies.bioportal import load_bioportal_csv_dictionary

def load_disease_dictionary():  
      
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
    
    # remove stopwords
    dictfile = "dicts/stopwords.txt"
    stopwords = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    diseases = {word:1 for word in diseases if word.lower() not in stopwords}  
    
    return diseases

def load_acronym_dictionary():    
    
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
        
    # filter by char length
    diseases = {word:1 for word in diseases if len(word) > 1}
    
    return diseases