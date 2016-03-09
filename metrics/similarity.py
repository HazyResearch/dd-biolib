

#relatedness(cui1, cui2, measure="lesk")

#similarity(cui1, cui2, measure="")


from __future__ import division

import networkx as nx
import numpy as np

#
# Path Finding Measures
#
# Most of these are from WordNet-style examinations of semantic similarity

def max_depth(G):
    """ Maximum depth of provided tree 
    TODO: This is a hack: do properly """
    paths = nx.all_pairs_shortest_path_length(G)
    maxdepth = -1
    for i in paths:
        maxdepth = max([maxdepth]+paths[i].values())
    return maxdepth


def depth(G,c):
    """Number of nodes between c and the root."""
    pass


def shortest_path(G, n1, n2):
    """Shortest path between n1 and n2."""
    if n1 not in G or n2 not in G:
        return None
    try:
        return nx.shortest_path(G,n1,n2)
    except:
        return None


def lcs(G, n1, n2):
    """ Least Common Subsumer (i.e., closest shared parent of nodes n1 and n2) """
    pass



def path_similarity(G, n1, n2):
    """Inverse of the length of the shortest path between n1 and n2, 
    otherwise -1 """
    path = shortest_path(G, n1, n2)
    return -1 if not path else 1.0/len(path)


def lch_similarity(G, n1, n2, scaled=False):
    """Leacock-Chodorow Similarity. Ratio of path length to depth with 
    logarithmic scaling. Optionally scale to unit interval. 
    """
    assert nx.is_tree(G)
    
    path = shortest_path(G, n1, n2)
    if not path:
        return -1 
    
    max_depth = 1 # max depth of G
    if not scaled:
        return np.log(2.0 * max_depth) - np.log(len(path))
    
    return 1.0 - (np.log(len(path))/np.log(2.0 * max_depth))
        

def wu_palmer_similarity(G, n1, n2):
    """Wu-Palmer Similarity. Scales the depth of the least common subsumer 
    by the length of the shortest path between n1 and n2"""
    pass




#
# Information Content
#

def information_content():
    pass

def resnik_similarity():
    pass