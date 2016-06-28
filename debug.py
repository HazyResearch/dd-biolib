import sys
import cPickle
from ddlite import *
from datasets import *

# ---------------------------------------------------------------------
#
# I. Load Candidates
#
# ---------------------------------------------------------------------

infile = "/users/fries/desktop/dnorm/all-ncbi-candidates.pkl"
candidates = Entities(infile)
model = CandidateModel(candidates)
msg = "Extracted {} features for each of {} mentions"
print msg.format(model.num_feats(), model.num_candidates())
