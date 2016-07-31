import unicodecsv

def load_bioportal_dictionary(filename, ignore_case=True):
    '''BioPortal Ontologies
    http://bioportal.bioontology.org/'''  
    reader = unicodecsv.reader(open(filename,"rb"),  delimiter=',', quotechar='"', encoding='utf-8')
    d = [line for line in reader]
  
    dictionary = {}
    for line in d[1:]:
        row = dict(zip(d[0],line))
        pref_label = row["Preferred Label"].lower() if ignore_case else row["Preferred Label"]
        dictionary[pref_label] = 1
        dictionary.update({t.lower() if ignore_case else t:1 for t in row["Synonyms"].split("|")})
        
    return dictionary