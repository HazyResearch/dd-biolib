'''
Given a directory of PMC articles, create a list of 
FTP links so that the example corpys snapshot can be 
downloaded. 

@author: fries
'''
import sys
import glob
import codecs

def load_file_list(fname):
    '''Load PMC file list. First line is a timestamp for download,
    all other rows are tab delimited data'''
    d = {}
    with codecs.open(fname,"rU","utf-8") as f:
        for i,line in enumerate(f):
            if i == 0:
                continue
            row = line.strip().split("\t")
            key = row[0].split("/")[-1].rstrip(".tar.gz")
            d[key] = row
    return d


URL = "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/"
inputdir = "/Users/fries/Desktop/hilda-demo/corpora/pmc-ortho/"

# load directory
filelist = glob.glob("{}*/*.nxml".format(inputdir))
filelist = [x.split("/")[-1].rstrip(".nxml") for x in filelist]

# name to FTP link mapping
ftplist = load_file_list("/users/fries/desktop/file_list.txt")

# dump FTP links
for fname in filelist:
    if fname not in ftplist:
        print>>sys.stderr,"MISSING", fname
        continue
    print "\t".join(ftplist[fname][0:2])
    

