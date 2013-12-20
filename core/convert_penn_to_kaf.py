from lxml import etree
from tree import Tree


## will be used as global variables to generate recursively the KAF constituent nodes
NOTER='nonter'
TER='ter'
EDGE='edge'
noter_cnt=0
ter_cnt=0
edge_cnt=0

##This function generates a "tree" xml element as defined in KAF from a string containing
##the penntreebank format and a list of term ids to do the linking
'''           
s = '(S (NP (DET The) (NN dog)) (VP (V ate) (NP (DET the) (NN cat))) (. .))'
ids = ['t0 t1','t2','t3','t4','t5','t6']
tree_node = create_constituency_layer(s, ids)
e = etree.ElementTree(element=tree_node)
e.write(sys.stdout,pretty_print=True)
'''
def convert_penn_to_kaf(tree_str,term_ids):
    global NOTER, TER, EDGE, noter_cnt,ter_cnt,edge_cnt

    this_tree = Tree(tree_str)
    
    for num, token in enumerate(this_tree.leaves()):
        position = this_tree.leaf_treeposition(num)
        token_id = term_ids[num]
        this_tree[position] = token_id
    

    ## TO include a root node
    my_noter_root_id = 'nter'+str(noter_cnt)
    noter_cnt+=1
    my_edge_root_id = 'tre'+str(edge_cnt)
    edge_cnt+=1
    
    linking_id, nodes = generate_nodes(this_tree)
    
    ## TO include a root node
    my_noter  = (NOTER,my_noter_root_id,'ROOT')
    my_edge = (EDGE,my_edge_root_id,my_noter_root_id,linking_id)
    nodes.insert(0,my_noter)
    nodes.insert(0,my_edge)
    
    
   
    ## non terminals
    nonter_nodes = []
    edges_nodes=  []
    ter_nodes = []
    nonter_heads = set()
    for n in nodes:
        if n[0] == NOTER:            
            _,nonter_id,label = n
            ##Checking the head
            if len(label)>=2 and label[-1]=='H' and label[-2]=='=':
                nonter_heads.add(nonter_id)
                label = label[:-2]
            ele = etree.Element('nt', attrib={'id':nonter_id,'label':label})
            nonter_nodes.append(ele)
        elif n[0] == EDGE:
            _,edge_id,node_to,node_from = n
            ele = etree.Element('edge',attrib={'id':edge_id,'from':node_from,'to':node_to})
            edges_nodes.append(ele)
        elif n[0] == TER:
            _,ter_id,span_ids = n
            ele = etree.Element('t',attrib={'id':ter_id})
            span = etree.Element('span')
            ele.append(span)
            for termid in span_ids.split(' '):
                target = etree.Element('target',attrib={'id':termid})
                span.append(target)
            ter_nodes.append(ele)
            
    root = etree.Element('tree')
    for nt in nonter_nodes:
        root.append(nt)
    
    for t in ter_nodes:
        root.append(t)
        
    for ed in edges_nodes:
        if ed.get('from') in nonter_heads:
            ed.set('head','yes')
        root.append(ed)        
    return root
        
##This is the recursive function to generate all the nodes behind a node
## It will generate all the terminal, non-terminal and edges nodes
def generate_nodes(node):
    global NOTER, TER, EDGE, noter_cnt,ter_cnt,edge_cnt
    if isinstance(node, str):  ## is a leaf
        # This is just a text (a token id)
        my_ter_id = "ter"+str(ter_cnt)
        ter_cnt+=1
        my_ter = (TER,my_ter_id,str(node))
        return my_ter_id,[my_ter]
    else:
        nodes = []
        my_nonter_id = 'nter'+str(noter_cnt)
        noter_cnt+=1
        my_nonter = (NOTER,my_nonter_id,node.node)
        nodes.append(my_nonter)
        
        for child in node:
            linking_id, subnodes = generate_nodes(child)
            nodes.extend(subnodes) 
            my_edge_id = 'tre'+str(edge_cnt)
            edge_cnt += 1
            my_edge = (EDGE,my_edge_id,my_nonter_id,linking_id)
            nodes.append(my_edge)
        return my_nonter_id,nodes
