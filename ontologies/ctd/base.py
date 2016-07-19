import codecs

def load_ctd_dictionary(filename, ignore_case=True):
    '''Comparative Toxicogenomics Database'''
    d = {}
    header = ['DiseaseName', 'DiseaseID', 'AltDiseaseIDs', 'Definition', 
              'ParentIDs', 'TreeNumbers', 'ParentTreeNumbers', 'Synonyms', 
              'SlimMappings']
        
    synonyms = {}
    dnames = {}
    with codecs.open(filename,"rU","utf-8",errors="ignore") as fp:
        for i,line in enumerate(fp):
            line = line.strip()
            if line[0] == "#":
                continue
            row = line.split("\t")
            if len(row) != 9:
                continue
            row = dict(zip(header,row))
             
            synonyms.update( dict.fromkeys(row["Synonyms"].strip().split("|")))
            dnames[row["DiseaseName"].strip()] = 1
    
    return {term.lower() if ignore_case else term:1 for term in synonyms.keys()+dnames.keys() if term}