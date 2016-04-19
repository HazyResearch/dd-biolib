import os
import glob

class Corpus(object):
    
    def __init__(self, path, parser, encoding="utf-8"):
        self.path = path
        self.parser = parser
        self.encoding = encoding

    def _get_files(self):
        if os.path.isfile(self.path):
            return [self.path]
        elif os.path.isdir(self.path):
            return [os.path.join(self.path, f) for f in os.listdir(self.path)]
        else:
            return glob.glob(self.path)    