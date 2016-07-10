import argparse
import sys
import re
import os
import config
import operator
import networkx as nx
from utils import database

class SemanticNetwork(object):
    """
    The UMLS Semantic Network defines 133 semantic types and 54 relationships 
    found in the UMLS Metathesaurus. There are two branches: Entity and Event
    
    https://www.ncbi.nlm.nih.gov/books/NBK9679/

    """
    def __init__(self,config):
        
        self.conn = database.MySqlConn(config.host, config.username, 
                                       config.dbname, config.password)
        self.conn.connect()
        self._networks = {}
        # load semantic group definitions
        self.abbrv, self.groups = self.__load_sem_groups()
        
        
    def __load_sem_groups(self):
        '''UMLS Semantic Groups '''
        module_path = os.path.dirname(__file__)
        fname = "%s/data/SemGroups.txt" % (module_path)
        abbrvs = {}
        isas = {}
        with open(fname,"rU") as f:
            for line in f:
                # format: ACTI|Activities & Behaviors|T051|Event
                abbrv,parent,tid,child = line.strip().split("|")
                abbrvs[abbrv] = parent
                if parent not in isas:
                    isas[parent] = {}
                isas[parent][child] = 1
        isas = {parent:isas[parent].keys() for parent in isas}    
        return abbrvs,isas
    
    
    def __build_semantic_network(self, relation="isa", directed=True, 
                                 simulate_root=True):
        """Load semantic network structure for a given relation."""
        
        sql_tmpl = """SELECT C.STY_RL1,C.RL,C.STY_RL2 FROM SRSTR AS C INNER 
        JOIN SRDEF AS A ON C.STY_RL1=A.STY_RL 
        INNER JOIN SRDEF AS B ON C.STY_RL2=B.STY_RL 
        WHERE A.RT='STY' AND B.RT='STY' AND C.RL='%s'"""
        
        query = sql_tmpl % (relation)
        results = self.conn.query(query)
        
        G = nx.DiGraph() if directed else nx.Graph()
        
        for row in results:
            child,_,parent = map(str,row)
            G.add_edge(parent,child)
        
        # Some concept graphs lack a shared root, so add one.
        root_nodes = [node for node in G if not G.predecessors(node)]
        if len(root_nodes) > 1 and simulate_root:
            root = "ROOT"
            for child in root_nodes:
                G.add_edge(root,child)
            
        return G
    
    def graph(self, relation="isa", directed=True, simulate_root=True):
        """Build a semantic network (graph) given the provided relation"""
        if relation not in self._networks:
            self._networks[relation] = self.__build_semantic_network(relation,directed)
        return self._networks[relation]
    
   