# -*- coding: utf-8 -*-
import sys
import cPickle
from ddlite import *
from datasets import *

# ---------------------------------------------------------------------
#
# I. Load Candidates
#
# ---------------------------------------------------------------------

candidates = Entities("cache/pmc-ortho-candidates.pkl")
model = CandidateModel(candidates)
msg = "Extracted {} features for each of {} mentions"
print msg.format(model.num_feats(), model.num_candidates())
