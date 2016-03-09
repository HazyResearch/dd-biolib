'''

'''
import networkx as nx
import matplotlib.pyplot as plt


def pprint_tree(T,root,indent=0):
    """Recursive print of tree structure"""
    print(('  ' * indent) + root)
    for child in T[root]:
        if child in T:
            pprint_tree(T,child,indent + 1)
        else:
            print(('  ' * indent) + child)


def draw(G):
    
    nx.write_dot(G,'/tmp/go.dot')
    pos=nx.graphviz_layout(G, prog='neato', args="-Goverlap=false -min_len=10")
    nx.draw(G,pos,node_size=5,with_labels=True,arrows=False,font_size=8)
    plt.draw()
    plt.show()
    '''
    pos=nx.spring_layout(G,k=1,iterations=400)
    labels = {name:name for i,name in enumerate(G.nodes())}
    #nx.draw(G,pos,node_size=1)
    nx.draw_shell(G)
    #nx.draw_networkx_labels(G,pos,labels,font_size=8)
    plt.draw()
    plt.show()
    '''