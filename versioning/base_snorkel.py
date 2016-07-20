'''
Snorkel Candidate Version

'''
import os
import sys
import glob
import hashlib
import cPickle
from ddlite import Relations
from datetime import datetime

def dict2str(d):
    '''Convert dictionary to tuple pair string'''
    return str(d).encode("utf-8",errors="ignore")


def checksum(s):
    '''Create checksum for input object'''
    if type(s) is dict:
        s = dict2str(s)
    elif type(s) in [list,tuple]:
        s = "|".join(sorted(list(s)))
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()


def cands2str(candidates):
    '''Convert DeepDive Relations object to string'''
    convert = lambda x:x.encode("utf-8",errors="ignore")
    rela_func = lambda x:["{}:{}".format(x.sentence["doc_id"], x.sentence["sent_id"])] + map(convert,x.mention1("words")) + map(convert,x.mention2("words"))
    entity_func = lambda x:["{}:{}".format(x.sentence["doc_id"], x.sentence["sent_id"])] + map(convert,x.get_span())
    get_row = rela_func if type(candidates) is Relations else entity_func
    # create string versions of candidates
    s = [":".join(get_row(c)) for c in candidates]
    return "|".join(sorted(s))


class CandidateVersioner(object):
    '''Create unique version ID for candidate set while saving to disk'''
    def __init__(self, rootdir, prefix="", dicts={}):
        self.rootdir = rootdir
        self.prefix = prefix
        self.dicts = dicts
        self._candidates = {}
        self.filename = None
        self.checksum = None
        
        
    def snapshot(self, name, candidates):
        self._candidates[name] = candidates
    
    
    def save(self):
        '''Save checksummed version of candidate set. This computes
        checksums based on dictionaries, input documents, and final
        candidate set'''
        candidates = reduce(lambda x,y:x+y, self._candidates.values())
        manifest = self._checksums(candidates, self.dicts)
        # dump candidates and log file
        ctype = "RELATIONS." if type(self._candidates) is Relations else "ENTITIES."
        prefix = self.prefix + "." if self.prefix else ""
        self.filename = "{}/{}{}{}".format(self.rootdir,prefix,ctype,manifest["uid"])
        
        cPickle.dump(self._candidates, open("{}.pkl".format(self.filename),"w"))
        self._write_log(self.filename,manifest)
        self.checksum = manifest["uid"]
        
        
    def load(self,checksum):
        filelist = glob.glob("{}*{}.pkl".format(self.rootdir,checksum))
        if len(filelist) > 1:
            print>>sys.stderr,"Warning: multiple matching checksums"    
        elif not len(filelist):
            print>>sys.stderr,"Error: snapshot not found"  
            return {}  
        
        fname = filelist[0]
        self._candidates = cPickle.load(open(fname,"rb"))
        self.filename = fname.strip(".pkl")
        self.checksum = checksum
        return self._candidates

            
    def _checksums(self, candidates, dicts):
        '''Compute MD5 checksums for all assets used to  
        create this candidate set'''
        manifest = {}
        # dictionary checksums
        for name,d in dicts.items():
            manifest["dictionary:{}".format(name)] = checksum(d) 
        # doc and candidate checksum
        doc_ids = sorted(set([c.sentence["doc_id"] for c in candidates]))
        manifest["doc_ids"] = checksum(doc_ids)
        manifest["candidates"] = checksum(cands2str(candidates))
        # some count data about candidates
        manifest["num_docs"] = len(doc_ids)
        manifest["num_candidates"] = len(candidates)
        # create unique checksum ID
        _,values = zip(*sorted(manifest.items()))
        values = map(str,values)
        manifest["uid"] = checksum(reduce(lambda x,y:x+y,values))
        return manifest
    
    
    def _write_log(self,filename,manifest):
        # write checksums to text file
        ts = datetime.now()
        outfile = "{}.checksums".format(filename)
        with open(outfile,'w') as f:
            f.write("{0:<22}{1:^11}{2:<32}\n".format("ts","=",str(ts)))
            for key,value in sorted(manifest.items()):
                f.write("{0:<22}{1:^11}{2:<32}\n".format(key,"=",value))
            
        


