#!/usr/bin/env python

'''

<SAB>.<ACRONYMS>.<STY>.txt
snomedct.terms.enzyme.txt
snomedct.abbrv.enzyme.txt

'''
from __future__ import print_function

import os
import re
import sys
import codecs
import argparse
import ddbiolib.ontologies.umls as umls

def create_dictionaries(term_types,outdir,dict_type="",min_size=250):
    
    metathesaurus = umls.Metathesaurus()
    semantic_network = metathesaurus.semantic_network.graph("isa")
    source_vocabs = metathesaurus.get_source_vocabulary_defs()
    
    for sty in semantic_network.nodes():
        for sab in source_vocabs:
            sty_str = sty.lower().replace(" ","_")
            dict_type_str = ".{}".format(dict_type) if dict_type else ""
            outfname = "{}{}.{}{}.txt".format(args.outdir,sty_str,sab,dict_type_str)
            if os.path.exists(outfname):
                print("{} exists, skipping".format(outfname))
                continue
            
            d = metathesaurus.dictionary(sty, source_vocab=[sab], term_types=term_types,
                                include_children=False)
            if len(d) < min_size:
                print("SKIPPING",sty,sab,len(d))
                continue 
            with codecs.open(outfname,"w","utf-8",errors="ignore") as f:
                f.write("\n".join(d))
            print(outfname)

def main(args):
    
    # UMLS metathesaurus
    #meta = umls.Metathesaurus()
    #norm = umls.MetaNorm(function=lambda x:x.lower()) if args.normalize else umls.MetaNorm(function=lambda x:x)
    
    #semantic_network = meta.semantic_network.graph("isa")
    #source_vocabs = meta.get_source_vocabulary_defs()

    min_size = 100
    
    # acronyms, abbreviations 
    term_types = ['AA','AB','ACR']
    create_dictionaries(term_types,args.outdir,dict_type="abbrv",min_size=min_size)
    
    # all terms
    #term_types = [tty for tty in umls.Metathesaurus().get_tty_list() if tty not in ['AA','AB','ACR']]
    #create_dictionaries(term_types,args.outdir,min_size=min_size)
    
   
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-t","--target", type=str, help="Target entity types, delimit list by |", default=None)
    parser.add_argument("-s","--source_vocab", type=str, 
                        help="limit to source vocabularies, delimit list by |", default=None)
    parser.add_argument("-n","--normalize", type=bool, 
                        help="make lowercase", default=False)
    
    parser.add_argument("-o","--outdir", type=bool, 
                        help="output directory", default=False)    
    
    parser.add_argument("-r","--exclude_subtrees", type=str, 
                        help="List of subtree root nodes to remove from the target ontology, delimit list by |", default=None)
    parser.add_argument("-e","--embeddings", type=str, help="word embeddings (default: none)", default=None)
    parser.add_argument("-k","--knn", type=int, help="expand dictionary with k nearest neighbors (default: none)", default=None)   
    args = parser.parse_args()
    
    main(args)