import codecs
import argparse
import itertools
from ddlite import *
from ddbiolib.datasets import PubMedCentralCorpus

def main(args):
    
    parser = SentenceParser()
    corpus = PubMedCentralCorpus(args.inputdir, parser, 
                                 cache_path=args.cachedir)
    
    sentences = [corpus[uid]["sentences"] for uid in corpus.documents.keys()[0:1000]]
    sentences = list(itertools.chain.from_iterable(sentences))

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--inputdir", type=str, help="indir file")
    parser.add_argument("-c","--cachedir", type=str, default="/tmp/", help="indir file")
    args = parser.parse_args()
    
    args.inputdir = ""
 
    main(args)