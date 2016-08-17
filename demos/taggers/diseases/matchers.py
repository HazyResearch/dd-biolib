import bisect, re
from ddlite_matchers import *
from collections import defaultdict


class NcbiDiseaseDictionaryMatch(NgramMatcher):
  """Selects according to ngram-matching against a dictionary i.e. list of words"""
  def init(self):
    # Load opts- this is from the kwargs dict
    self.label         = self.opts['label']
    self.dictionary    = self.opts['d']
    self.match_attrib  = self.opts.get('match_attrib', 'words')
    self.ignore_case   = self.opts.get('ignore_case', True)
    self.longest_match = self.opts.get('longest_match', True)

    # Split the dictionary up by phrase length (i.e. # of tokens)
    self.dl = defaultdict(lambda : set())
    for phrase in self.dictionary:
        self.dl[len(phrase.split())].add(phrase.lower() if self.ignore_case else phrase)
    self.dl.update((k, frozenset(v)) for k,v in self.dl.iteritems())

    # Get the *DESC order* ngram range for this dictionary
    self.ngr = range(max(1, min(self.dl.keys())), max(self.dl.keys())+1)[::-1]

  def _apply(self, s, idxs=None):
    """
    Take in an object or dictionary which contains match_attrib
    and get the index lists of matching phrases
    If idxs=None, consider all indices, otherwise constrain to subset of idxs
    """
    seq = self._get_attrib_seq(s)

    # If idxs=None, consider the full index range, otherwise only subseqs of idxs
    start = 0 if idxs is None else min(idxs)
    end   = len(seq) if idxs is None else max(idxs)+1
    L     = len(seq) if idxs is None else len(idxs)

    # NOTE: We assume that idxs is a range of consecutive indices!
    if L != end - start:
      raise ValueError("Candidates must be over consecutive spans of indices")

    # Keep track of indexes we've already matched so that we can e.g. keep longest match only
    matched_seqs = []

    # Loop over all ngrams
    for l in filter(lambda n : n <= L, self.ngr):
      for i in range(start, end-l+1):
        ssidx = range(i, i+l)

        # If we are only taking the longest match, skip if a subset of already-tagged idxs
        if self.longest_match and any(set(ssidx) <= ms for ms in matched_seqs):
          continue
        phrase = ' '.join(seq[i:i+l])
        if phrase.lower() == 'deficiency' and i+l<L and seq[i+l].lower() in ['in', 'of']:
            continue
        phrase = phrase.lower() if self.ignore_case else phrase
        if phrase in self.dl[l]:
          min_idx = min(ssidx)
          max_idx = max(ssidx)
          if (max_idx+1<L and seq[max_idx+1].lower() in ['deficiency', 'deficient', 'deficienty', 'syndrome']):
            ssidx = range(min_idx, max_idx+2)
          min_idx = min(ssidx)
          max_idx = max(ssidx)
          if (max_idx+2<L and seq[max_idx+1].lower() in ['type', 'class', 'stage', 'factor'] and (seq[max_idx+2].lower() in ['i', 'ii', 'iii', 'vi', 'v', 'vi', '1a', 'iid', 'a', 'b', 'c', 'd'] or seq[max_idx+2].isdigit())):
            ssidx = range(min_idx, max_idx+3)
          min_idx = min(ssidx)
          max_idx = max(ssidx)
          if (min_idx-2>=0 and seq[min_idx-2].lower() in ['type', 'class', 'stage', 'factor'] and (seq[min_idx-1].lower() in ['i', 'ii', 'iii', 'iv', 'v', 'vi', '1a', 'iid', 'a', 'b', 'c', 'd'] or seq[min_idx-1].isdigit())):
            ssidx = range(min_idx-2, max_idx+1)
          min_idx = min(ssidx)
          max_idx = max(ssidx)
          if (min_idx-2>=0 and seq[min_idx-2].lower() in ['deficiency'] and seq[min_idx-1].lower() in ['of']):
            ssidx = range(min_idx-2, max_idx+1)
          min_idx = min(ssidx)
          max_idx = max(ssidx)
          if (min_idx-1>=0 and seq[min_idx-1].lower() in ['inherited']):
            ssidx = range(min_idx-1, max_idx+1)
          if any(set(ssidx) <= ms for ms in matched_seqs):
            continue
          matched_seqs.append(frozenset(ssidx))
          yield list(ssidx), self.label
    checkbox = []
    matched_seqs = sorted(matched_seqs, key=lambda x:min(x))
    for i in range(len(matched_seqs)):
        if i in checkbox: continue
        min_idx = min(list(matched_seqs[i]))
        max_idx = max(list(matched_seqs[i]))
        haveone = True
        checked = False
        checkbox.append(i)
        while haveone:
            haveone = False
            for j in range(len(matched_seqs)):
                if j not in checkbox and (max_idx + 1 == min(list(matched_seqs[j])) or (max_idx + 2 == min(list(matched_seqs[j])) and seq[max_idx + 1].lower() in ['and/or', 'of', 'and', 'or'])):
                    checkbox.append(j)
                    max_idx = max(list(matched_seqs[j]))
                    haveone = True
                    checked = True
                    break
        if checked:
            pass
            #yield list(range(min_idx, max_idx + 1)), self.label