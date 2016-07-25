from nltk.tree import Tree
import re

s = '''
(ROOT
  (S
    (S
      (NP (PRP It))
      (VP (VBD was)
        (UCP
          (ADJP (JJ rare))
          (, ,)
          (CONJP (IN as) (RB not))
          (VP (VBN observed)
            (PP (IN in)
              (NP (NNS controls)))))))
    (, ,)
    (CC but)
    (S (RB not)
      (VP (VBG segregating)
        (PP (IN with)
          (NP (DT the) (NN BFIC) (NN phenotype)))))
    (. .)))
'''

def parse_tree(t):
    #if t[0]=="(" and t[-1]==")":
    m = re.search("(^\(.+)\s+(.+\)$)",t.strip(),re.DOTALL)
    
    if m:
        print t.replace(m.group(1),"")
        #parse_tree(m.group(0))
    #print ""



#print s
#parse_tree(s)
m = re.search("(^\(.+)\s+(.+\)$)",s.strip(),re.DOTALL)
print m.group(1)
#m = re.search("^\((.+)\)$",t,re.DOTALL)