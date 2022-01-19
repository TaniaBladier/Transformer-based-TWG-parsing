import sys, os
#import time
current_dir = os.getcwd()
sys.path.insert(1, current_dir)

from discodop_n.tree import writediscbrackettree, writebrackettree, DrawTree, Tree, ptbunescape
from discodop_n.treetransforms import removeemptynodes
from discodop_n.treebank import (NegraCorpusReader, BracketCorpusReader, brackettree, writeexporttree, LEMMA, MORPH, FUNC, READERS)

from typing import Sequence

punc_list = [',', '.']

reader = NegraCorpusReader

def find_node_in_upper_subtree(stree,label_strings):
    if stree.parent and stree.parent.label in label_strings:
        return stree.parent
    else:
        if stree.parent and stree.parent.parent:
            return find_node_in_upper_subtree(stree.parent, label_strings)


def find_another_sibling_with_same_label(stree, label_string):
    if stree.parent and not (len(stree.parent) == 2 and label_string in stree.parent.label):
        lst_of_children = [k.label for k in stree.parent]
        if label_string in lst_of_children:
            nodeidx = lst_of_children.index(label_string)
            return stree.parent[nodeidx]

def flatten(input):
    return [i for el in input
            for i in (flatten(el)
                      if (isinstance(el, Sequence) and not isinstance(el, str))
                      else [el])
            ]


def span_representation(lst):
    sp_repr = '_'.join(str(x) for x in flatten(lst))
    return sp_repr


def find_spans_in_list(lst):
    cluster_points = []
    chunks = []

    n = 0
    while n < len(lst) - 1:
        if lst[n + 1] - lst[n] != 1:
            cluster_points.append(n + 1)
        n += 1

    c = 0
    l = len(lst)
    if len(cluster_points) > 0:
        for x in cluster_points:
            chunk = lst[c:x]
            chunks.append(chunk)
            c = x
        last_chunk = lst[cluster_points[-1]:l]
        chunks.append(last_chunk)
    if len(cluster_points) == 0:
        chunks.append(lst[0:])

    chunks_new = [span_representation(x) for x in chunks]
    return chunks_new


def has_crossing_branches(tree):

    for a in tree.subtrees(lambda n: isinstance(n[0], Tree)):
        a.children.sort(key=lambda n: min(n.leaves()))

    for subtree in tree.subtrees():

        # split the children such that each sequence of children dominates
        # a continuous block of terminals
        blocks = []
        for child in subtree:
            if len(blocks) == 0:
                blocks.append([])
            else:
                last_terminal = blocks[-1][-1].leaves()[-1]
                if child.leaves()[0] > last_terminal + 1:
                    blocks.append([])
            blocks[-1].append(child)

        if len(blocks) > 1:
            if len(find_spans_in_list(sorted(flatten([[h.leaves() for h in x] for x in blocks])))) > 1:
                return True


def postpostprocess(tree):
    for stree in tree.subtrees():
        stree.label = stree.label.replace('???', '')
        stree.label = stree.label.split('[')[0]
        stree.label = stree.label.split('&')[0]
    return tree


def left_pos_tag(tree, maintree):
    for stree in maintree.subtrees():
        if len(stree.leaves()) == 1 \
            and stree.leaves()[0] == tree.leaves()[0] - 1 \
            and isinstance(stree[0],int):
            return stree.label


def right_pos_tag(tree, maintree):
    for stree in maintree.subtrees():
        if len(stree.leaves()) == 1 \
            and stree.leaves()[0] == tree.leaves()[-1] + 1 \
            and isinstance(stree[0],int):
            return stree.label

def postprocess(tree, sent):
    for stree in tree.subtrees():
        if stree.label == "AP" and stree.parent and stree.parent.label == 'NUC' and stree.height() == 5:
            try:
                stree.label = 'A'
                stree[0].prune()
                stree[0].prune()
                stree[0].prune()
            except:
                pass
    for stree in tree.subtrees():
        if stree.parent and stree.parent.label== stree.label and len(stree.parent) ==1:
            stree.parent.prune()
        
    


def left_neighbour_word(tree,sent):
    left_word_idx = tree.leaves()[0]-1
    return sent[left_word_idx]


def right_neighbour_word(tree,sent):
    try:
        right_word_idx = tree.leaves()[-1] + 1
        return sent[right_word_idx]
    except:
        return None

def nearest_right_sibling(node):
    if node.parent and len(node.parent) > 1: #and not isdisc(node.parent):
        for ch in node.parent:
            #print("ch", ch)
            if ch.parent_index - node.parent_index == 1:
                return ch
            else:
                return None


def find_node_in_upper_subtree(stree,label_strings):
    if stree.parent and stree.parent.label in label_strings:
        return stree.parent
    else:
        if stree.parent and stree.parent.parent:
            return find_node_in_upper_subtree(stree.parent, label_strings)



def find_minimal_branching_tree(stree):
    if stree.parent and len(stree.parent) > 1:
        return stree.parent
    elif stree.parent and len(stree.parent) == 1:
        return find_minimal_branching_tree(stree.parent)
    else:
        return None


def orig_parent_label(labelstr):
    if '[PS' in labelstr:
        return labelstr.split('PS=')[1].replace(']', '') 

def orig_label(labelstr):
    if '[PS' in labelstr:
        return labelstr.split('[PS=')[0] 


def reattach_to_upper_subtree(stree, lst_of_labels):
    upper_stree = find_node_in_upper_subtree(stree, lst_of_labels)
    if upper_stree:
        upper_stree.append(stree.detach())


def get_right_leaf_number(n):
    return n.leaves()[-1]


def find_minimal_tree_with_several_children(leaf_idx, tree):
    lst_of_candidate_trees = []
    for stree in tree.subtrees():
        if leaf_idx in stree.leaves():
            if len(stree.leaves()) > 1:
                lst_of_candidate_trees.append(stree)
            if len(stree.leaves()) == 1:
                lst_of_candidate_trees.insert(0, stree)

    return lst_of_candidate_trees[-1]


def find_nearest_new_right_parent(node, tree):

    rightmost_leaf_number = get_right_leaf_number(node)

    right_neighbour_leaf_number = rightmost_leaf_number + 1

    if right_neighbour_leaf_number >= 0 and right_neighbour_leaf_number < len(tree.leaves()):
        return find_minimal_tree_with_several_children(right_neighbour_leaf_number, tree)


def isfirstchild(stree):
    if stree.parent:
        lst_labels = [x.label for x in stree.parent]
        if lst_labels.index(stree.label) == 0:
            return True



def backtransform(tree, sent):

    for stree in tree.subtrees():
        if stree.parent and stree.parent.label== stree.label and len(stree.parent) ==1 and len (stree) > 2:

            stree.parent.insert(0, stree[-1].detach())
        elif stree.parent and stree.parent.label== stree.label and len(stree.parent) ==1 and len (stree) == 2:
            stree.parent.append(stree[-1].detach())
        elif stree.parent and stree.parent.label== stree.label and len(stree.parent) ==1 and len (stree) == 1 and not stree.label == "NUC":
            if stree.parent.parent.parent:
                stree.parent.parent.parent.append(stree.parent.detach())
    

    for stree in tree.subtrees():
        if stree.label == "CLM" and stree.parent and len(stree.parent) > 1 and stree.parent.height() > 3:
            if not (stree.parent.label in ['CLAUSE', 'CORE'] and isfirstchild(stree)):
                minimal_branching_parent = find_minimal_branching_tree(stree)
                minimal_branching_parent.append(stree.detach())
  
    
    for stree in tree.subtrees():
        if (stree.label == "AP" 
            and stree.parent and stree.parent.label == 'NUC'
            and stree[0] and stree[0].label == 'CORE_A'):
            stree[0].prune()
            stree[0].prune()
            stree.prune()
    

    for stree in tree.subtrees():
        if '[PS=' in stree.label:
            par_label = orig_parent_label(stree.label)
            or_label = orig_label(stree.label)
            if par_label != 'NUC':
                stree.label = or_label
                reattach_to_upper_subtree(stree, [par_label])
            elif par_label == 'NUC':
                sibling_tree = find_another_sibling_with_same_label(stree, par_label)
                if sibling_tree:
                    try:
                        new_label = stree[0].label
                        stree[0].prune()
                        stree.label = new_label
                        sibling_tree.append(stree.detach())
                    except:
                        pass
                #else:
                    #reattach_to_upper_subtree(stree, ["NUC"])
                    
    
    for stree in tree.subtrees():
        if stree.label == 'PrCS' and stree.parent and not stree.parent.label in ['CLAUSE', 'CLAUSE-PERI', 'SENTENCE-PERI', 'SENTENCE']:
            reattach_to_upper_subtree(stree, ['CLAUSE', 'CLAUSE-PERI'])

    for stree in tree.subtrees():
        try:
            if stree.label == 'CLM' and nearest_right_sibling(stree) == None and stree.parent and len(stree.parent) > 1 and stree.parent.height() > 3:
                new_parent = find_nearest_new_right_parent(stree, tree)
                if not (stree.parent.label in ['CLAUSE', 'CORE'] and isfirstchild(stree)) and new_parent.height() > 3:
                    if new_parent:
                        new_parent.append(stree.detach())
        except:
            pass
    print(DrawTree(tree, sent))
    

    for a in tree.subtrees(lambda n: isinstance(n[0], Tree)):
        a.children.sort(key=lambda n: min(n.leaves()))

    for stree in tree.subtrees():
        try:
            if stree.label == 'CLM' and stree.parent and len(stree.parent) == 3 and stree.parent[1].label == 'CLM' and stree.parent.height() > 3:
                stree.parent[2].append(stree.detach())
        except:
            pass

    postprocess(tree,sent)
    return tree, sent


def conv(tree, sent):
    # ensure there is a ROOT label, different from S
    #if tree.label != 'ROOT':
    #    tree = ParentedTree('ROOT', [tree])
    #try:
    #print(tree)
    backtransform(tree, sent)
    #removeemptynodes(tree, sent)
   # reversetransform(tree, sent, ('APPEND-FUNC', ))

    return tree
    #except:
        #return tree
