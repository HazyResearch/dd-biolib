
import umls

import os, sys, re, cPickle
from ddlite import *
      

def clean(d):
    '''Clean up UMLS dictionary my removing terms that are numbers or single
    letters (they are too noisy to trust).
    '''
    return [term for term in d if len(term) > 1 and not term.isdigit()]



doc_string = "Ten female pigs (Danish Landrace breed, weighing from 67 to 77 kg) were used. On day 0, trauma-induced implant-associated S. aureus osteomyelitis was induced in the proximal metaphysis of the right tibia. Postoperatively, the pigs received buprenorphine (Temgesic; 0.02 mg/kg intramuscularly) twice, with an eight-hour interval, and eight hours after the last injection of Temgesic, the analgesia was maintained with meloxicam (Metacam; 0.3 mg/kg by mouth) every twenty-four hours. Five days later, measurements of cefuroxime were conducted using microdialysis in the implant-related bone cavity, adjacent infected cancellous bone, and infected subcutaneous tissue as well as in the healthy cancellous bone and subcutaneous tissue in the contralateral leg. Bone measurements were obtained in drill-holes. For comparison, measurements of the corresponding plasma concentration were also obtained. When the last samples were collected, the animals were killed using pentobarbital."

doc = cPickle.load(open("/Users/fries/Desktop/doc.pkl","r"))

'''
parser = SentenceParser()
sentences = []
for sent in parser.parse(doc_string):
    sentences += [sent]
cPickle.dump(sentences,open("/users/fries/desktop/doc.pkl","wb"))
'''

extractor = umls.UmlsMatch('A',semantic_types=["Substance"],ignore_case=True)

entities = Entities(extractor,doc)
for ent in entities.entities:
    print(ent)

sys.exit()





#entities = Entities(DictionaryMatch('A', anatomy, ignore_case=True),doc)


#for term in sorted(dictionary,key=lambda x:len(x.split()),reverse=1):
#    print(term)

'''
for sty in meta.semantic_network.groups["Anatomy"]:
    dictionary += meta.dictionary(sty)
    
print(len(dictionary))
for term in dictionary:
    print(term)

#UmlsMatch('X', semantic_types=[], include_ancestors=0, ignore_case=True)
'''