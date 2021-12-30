import sys, os


from discodop_n.tree import writediscbrackettree, writebrackettree, DrawTree, Tree, ptbunescape
from discodop_n.treetransforms import removeemptynodes, isdisc
from discodop_n.treebank import (NegraCorpusReader, BracketCorpusReader, brackettree, writeexporttree, LEMMA, MORPH, FUNC, READERS)

from typing import Sequence

punc_list = [',', '.']


def nearest_right_sibling(node):
    if node.parent and len(node.parent) > 1 and not isdisc(node.parent):
        for ch in node.parent:
            if ch.parent_index - node.parent_index == 1:
                return ch



def find_node_in_upper_subtree(stree,label_strings):
    if stree.parent and stree.parent.label in label_strings:
        return stree.parent
    else:
        if stree.parent and stree.parent.parent:
            return find_node_in_upper_subtree(stree.parent, label_strings)


def find_another_sibling_with_same_label(stree, label_string):
    if stree.parent and not (len(stree.parent) == 2 and label_string in stree.parent.label):
        if len([stree.parent.index(x) for x in stree.parent if not isinstance(x,int)
                                                               and x.label.split('&')[0].split('[')[0] == label_string]) == 2:
            if not (len(stree.parent) == 3 and stree.parent[1].label == 'CLM'):
                return [stree.parent.index(x) for x in stree.parent if x.label.split('&')[0].split('[')[0] == label_string]


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
        stree.label = stree.label.replace('???', '')
        stree.label = stree.label.split('[')[0]
        stree.label = stree.label.split('&')[0]
    
    for clauseperi in tree.subtrees(lambda n: 'CLAUSE-PERI' in n.label):
        parent = clauseperi.parent
        if parent and not 'NUC_N' in parent.label and parent[0].label == 'NUC_N' and len(parent[0]) == 1:
            clauseperi.label = clauseperi.label.split('[')[0]
            parent[0].append(clauseperi.detach())
        elif parent and not 'NUC_N' in parent.label and len(parent) > 1 and parent[1].label == 'NUC_N' and not parent[0].label == 'NUC_N':
            clauseperi.label = clauseperi.label.split('[')[0]
            parent[1].append(clauseperi.detach())
        elif parent and 'SENTENCE' in parent.label and parent[0].label == 'CLAUSE':
            clauseperi.label = clauseperi.label.split('[')[0]
            parent[0].append(clauseperi.detach())
        #elif parent and 'NP' in parent.label and 'CORE_N' in parent[0].label:
        #    clauseperi.label = clauseperi.label.split('[')[0]
         #   parent[0].append(clauseperi.detach())
        elif parent and not 'NUC_N' in parent.label and len(parent) > 3 and parent[2].label == 'NUC_N':
            clauseperi.label = clauseperi.label.split('[')[0]
            parent[2].append(clauseperi.detach())
        elif ((left_neighbour_word(clauseperi, sent) in punc_list
              and right_neighbour_word(clauseperi, sent) in punc_list)
            or (sent[clauseperi.leaves()[0]].lower() in punc_list and sent[clauseperi.leaves()[-1]].lower())
            and not clauseperi.parent.label == 'NP'):
            if clauseperi.parent.label != 'CLAUSE' :
                clause_parent = find_node_in_upper_subtree(clauseperi.parent,'CLAUSE')
                if clause_parent:
                    clause_parent.append(clauseperi.detach())
        #elif parent and parent.label == 'CORE':
        #    parent.parent.append(clauseperi.detach())

    for stree in tree.subtrees():
        if [x.label for x in stree if not isinstance(x,int)].count('CORE') == 3 and not len(stree) == 3:
            if not [x.label for x in stree if not isinstance(x,int)] == ['CORE', 'CORE', 'CLM', 'CORE']:
                lst = [x for x in stree]
                lst_idxs = [lst.index(y) for y in lst if y.label == 'CORE']
                stree[lst_idxs[1]].prune()
                stree[lst_idxs[2]].prune()
                stree[lst_idxs[0]].append(stree[lst_idxs[1]].detach())
                stree[lst_idxs[0]].append(stree[lst_idxs[2]-1].detach())
            else:
                lst = [x for x in stree]
                lst_idxs = [lst.index(y) for y in lst]
                stree[lst_idxs[0]].append(stree[lst_idxs[1]].detach())
                stree[lst_idxs[2]].append(stree[lst_idxs[1]].detach())

    for auxtns in tree.subtrees(lambda n: 'AUX-TNS' in n.label):
         if (auxtns.parent and auxtns.parent.label == 'CORE'
             and auxtns.parent.parent and auxtns.parent.parent.label == 'CORE'
                and auxtns.parent.parent.parent and auxtns.parent.parent.parent.label == 'NUC'):
             auxtns.parent.parent.parent.append(auxtns.detach())

    # put together two nucs which are not under nuc
    for nuc in tree.subtrees(lambda n: 'NUC' in n.label):
        two_idx = find_another_sibling_with_same_label(nuc, 'NUC')
        if two_idx and not nuc.parent.label == 'NUC':#(two_idx[1] - two_idx[0] < 2):
           # print('173')
            nuc.parent[two_idx[0]].append(nuc.parent[two_idx[1]].detach())
            nuc.label = nuc.label.split('[')[0]

            if len(nuc) == 2 and "NUC" in nuc[1].label and not nuc[1][0].label == 'AUX':
                nuc[1].label = 'NUC'
                nuc[0].spliceabove('NUC')
            elif len(nuc) == 2 and "NUC" in nuc[1].label and nuc[1][0].label == 'AUX':
                nuc[1].prune()

    # put together two nucs which are not under nuc
    for coren in tree.subtrees(lambda n: 'CORE_N' in n.label):
        if (len(coren) == 3 and coren[0].label == 'NUC_N'
            and coren[2].label == 'NUC_N' and coren[0][0].label in ('AP-PERI', 'ADVP-PERI')):
            coren[2].prune()
            coren[0].append(coren[2].detach())

    for advpperi in tree.subtrees(lambda n: 'ADVP-PERI' in n.label):

        parent = advpperi.parent
        if parent.label == 'CORE_N' and len(parent) > 2 \
                and parent[2].label in ['QP', 'QP-PERI'] \
                and not sent[advpperi.leaves()[0]].lower() in ['approximately']:
            parent[2][0].append(advpperi.detach())
        if (sent[advpperi.leaves()[0]].lower() in ['however', ',']
            and parent.label == 'CORE'):# and parent.parent.parent.parent.label == 'CORE'):
            parent.parent.append(advpperi.detach())
        #if parent.label == 'PoDP':
        if parent.label == 'NUC' and parent[0].label == 'AUX-TNS':
             parent.parent.append(advpperi.detach())
        if parent.label == 'NUC' and sent[advpperi.leaves()[-1]].lower() in ['just', 'also',
                                                                            'quite', 'continuously', 'almost', 'only',
                                                                            'still']:
             parent.append(advpperi.detach())
        if  parent.label == 'CORE':
            parent.append(advpperi.detach())

    for v in tree.subtrees(lambda n: n.label == 'V'):
        parent = v.parent
        if parent.label == 'CORE':
            for x in parent:
                if x.label == 'NUC' and len(x) == 2 and x[1].label == 'NUC':
                    x[1].append(v.detach())
                elif x.label == 'NUC':
                    x.append(v.detach())

    for opneg in tree.subtrees(lambda n: n.label in ['OP-NEG', 'OP-MOD']):
        parent = opneg.parent
        if (opneg.parent.label == 'CORE'
            and opneg.parent.parent != None
            and opneg.parent.parent.label == 'CORE' and len(opneg.parent.parent) == 2
            and [x.label for x in opneg.parent.parent if not isinstance(x,int)].count('CORE') == 2
            and not sent[opneg.leaves()[0]] in ['ought']):
            #and opneg.parent.parent[1][0].label != 'CLM'
           #     and not sent[opneg.parent.parent[1].leaves()[0]] in ['to', 'and']):

            parent.parent.append(opneg.detach())
    # easy repairs like op-def
    for opmod in tree.subtrees(lambda n: 'OP-MOD' in n.label):
        parent = opmod.parent
        if parent and parent.label != 'CORE':
            opmod.label = opmod.label.split('[P')[0]
            core_parent = find_node_in_upper_subtree(parent, 'CORE')
            if core_parent:
                core_parent.append(opmod.detach())


    for clause in tree.subtrees(lambda n: 'CLAUSE' in n.label):
        if len(clause) == 3 \
                and clause[0].label == 'PP-PERI'\
                and clause[1].label == 'CORE' \
                and clause[2].label == 'CLAUSE':
            clause[2][0].append(clause[0].detach())


    for npperi in tree.subtrees(lambda n: 'NP-PERI' in n.label):
        if ((left_neighbour_word(npperi, sent) in punc_list
              and right_neighbour_word(npperi, sent) in punc_list)
            or (sent[npperi.leaves()[0]].lower() in punc_list and sent[npperi.leaves()[-1]].lower())):
            if npperi.parent.label in ['AP', 'AP-PERI']:
                #print('144!!')
                clause_parent = find_node_in_upper_subtree(npperi.parent,'CLAUSE')
                if clause_parent:
                    clause_parent.append(npperi.detach())


    for core in tree.subtrees(lambda n: 'CORE' in n.label):
        if len(core) == 3 \
                and core[0].label.split('[')[0] == 'NP'\
                and core[1].label.split('[')[0]  == 'NUC' \
                and core[1][0].label.split('[')[0]  == 'AUX-TNS'\
                and core[2].label.split('[')[0]  == 'NUC':
            core[1].prune()
            core[2].append(core[1].detach())

    for clause in tree.subtrees(lambda n: 'CLAUSE' in n.label):
        if len(clause) == 3 \
                and clause[0].label.split('[')[0] == 'CORE'\
                and clause[1].label.split('[')[0]  == 'CORE' \
                and clause[2].label.split('[')[0]  == 'CLAUSE-PERI':
            clause[1].append(clause[2].detach())

    for ppperi in tree.subtrees(lambda n: 'PP-PERI' in n.label):
        if ppperi.parent.label == 'NUC':
            if ppperi.parent.parent.label == 'CORE':
                ppperi.parent.parent.append(ppperi.detach())

    for nucq in tree.subtrees(lambda n: 'NUC_Q' in n.label):
        if nucq.parent.label == 'CORE':
            for x in nucq.parent:
                if x.label == 'NP':
                    x[0].append(nucq.detach())


    for advpperi in tree.subtrees(lambda n: n.label == 'ADVP-PERI'):
        if sent[advpperi.leaves()[0]] in ['partially']:
            parent = advpperi.parent
            if advpperi.parent.label == 'NUC_A':
                parent.parent.append(advpperi.detach())

    for pp in tree.subtrees(lambda n: n.label == 'PP'):
        if sent[pp.leaves()[0]] in ['until']:
            pp.label = 'PP-PERI'

    for auxtns in tree.subtrees(lambda n: n.label == 'AUX-TNS'):
        if (sent[auxtns.leaves()[0]] in ['were'] and sent[auxtns.leaves()[0] +1] in ["n't"]):
                #or (auxtns.parent.label == 'NUC' and right_pos_tag(auxtns,tree) in ['V'] and sent[auxtns.leaves()[0]] in ['are']):
            auxtns.label = 'OP-TNS'
            clause_parent = find_node_in_upper_subtree(auxtns.parent, 'CLAUSE')
            if clause_parent:
                clause_parent.append(auxtns.detach())


    for qnt in tree.subtrees(lambda n: n.label == 'QNT'):
        if len(qnt.leaves()) > 0:
            if sent[qnt.leaves()[0]] in ['all']:
                if qnt.parent.label == 'NPIP':
                    qnt.parent.label = 'NUC_Q'
                    qnt.parent.spliceabove('CORE_Q').spliceabove('QP-PERI')

    for adv in tree.subtrees(lambda n: n.label == 'A'):
        if sent[adv.leaves()[0]] in ['apart'] and left_pos_tag(adv,tree) == 'V':
            adv.label = 'ADV'
            if adv.parent.label == 'NUC_A' \
                and adv.parent.parent.label == 'CORE_A' \
                and adv.parent.parent.parent.label in ['AP', 'AP-PERI']:
                adv.parent.label = 'NUC_ADV'
                adv.parent.parent.label = 'CORE_ADV'
                adv.parent.parent.parent.label = 'ADVP'
                adv.parent.parent.parent.parent.parent.append(adv.parent.parent.parent.detach())
    for adv in tree.subtrees(lambda n: n.label == 'ADV'):
        #try:
        if sent[adv.leaves()[0]] in ['Earlier']:
            print("334")
            adv.label = 'A'
            if adv.parent.label == 'NUC_ADV' \
                    and adv.parent.parent.label == 'CORE_ADV' \
                    and adv.parent.parent.parent.label in ['ADVP', 'ADVP-PERI']:
                adv.parent.label = 'NUC_A'
                adv.parent.parent.label = 'CORE_A'
                adv.parent.parent.parent.label = 'AP-PERI'
        #except:
            #pass


    for auxtns in tree.subtrees(lambda n: n.label == 'AUX-TNS'):
        if auxtns.parent.label == 'NUC'\
                and left_pos_tag(auxtns,tree) in ['PRO','PRO-WH'] and right_pos_tag(auxtns,tree) in ['PRO','PRO-WH'] :
            auxtns.label = 'V'




    for nuc in tree.subtrees(lambda n: n.label == 'NUC'):
        if nuc.parent.label == 'NUC' and [x.label for x in nuc.parent if not isinstance(x,int)].count('NUC') == 1:
            nuc.prune()
    for vpart in tree.subtrees(lambda n: n.label == 'V-PART'):
        if sent[vpart.leaves()[0]].endswith('ly'):
            if vpart.parent.label == 'NUC_A' \
                and vpart.parent.parent.label == 'CORE_A' \
                and vpart.parent.parent.parent.label in ['AP', 'AP-PERI']:
                vpart.label = 'ADV'
                vpart.parent.label = 'NUC_ADV'
                vpart.parent.parent.label = 'CORE_ADV'
                vpart.parent.parent.parent.label = 'ADVP-PERI'

    for advpperi in tree.subtrees(lambda n: n.label == 'ADVP-PERI'):
        if advpperi.parent.label == 'NUC':
            idx_of_advpperi = advpperi.parent.index(advpperi)
            for x in advpperi.parent:
                if x.label == 'AP' and advpperi.parent.index(x) - idx_of_advpperi == 1 and not isinstance(x[0][0], int):
                    x[0].append(advpperi.detach())

    for nucp in tree.subtrees(lambda n: n.label == 'NUC_P'):
        if sent[nucp.leaves()[0]] == 'into' and sent[nucp.leaves()[0]-1] == 'break':
            nucp.parent.prune()
            nucp.prune()

    for sentence in tree.subtrees(lambda n: n.label == 'SENTENCE'):
        if sentence.parent and sentence.parent.label == 'CLAUSE' and len(sentence.parent) == 2 \
            and sentence.parent[0].label == 'SENTENCE' and sentence.parent[1].label == 'CORE':
            sentence.prune()


    for pro in tree.subtrees(lambda n: n.label == 'PRO'):
        if sent[pro.leaves()[0]] in ["'Ave"] and pro.parent.label == 'NP':
            pro.label = 'V'
            pro.parent.label = 'NUC'

    for stree in tree.subtrees():
        if [x.label for x in stree if not isinstance(x,int)].count('PoDP') > 1:
            for x in stree:
                if x.label == 'PoDP':
                    x.prune()
    

    for core in tree.subtrees(lambda n: n.label == 'CORE'):
        if core.parent and core.parent.label == 'CORE' and len(core.parent) == 1 and core[0].label == 'CORE':
            core.parent.append(core[0].detach())
    

    return tree


def left_neighbour_word(tree,sent):
    left_word_idx = tree.leaves()[0]-1
    return sent[left_word_idx]


def right_neighbour_word(tree,sent):
    try:
        right_word_idx = tree.leaves()[-1] + 1
        return sent[right_word_idx]
    except:
        return None


def backtransform(tree, sent):

    # easy repairs like op-tns
    for optns in tree.subtrees(lambda n: 'OP-TNS' in n.label):
        parent = optns.parent
        if parent and not 'CLAUSE' in parent.label.split('[')[0]:
            optns.label = optns.label.split('[')[0]
            clause_parent = find_node_in_upper_subtree(parent,'CLAUSE')
            if clause_parent:
                clause_parent.append(optns.detach())

    # easy repairs like op-tns
    for optns in tree.subtrees(lambda n: 'TNS-OP' in n.label):
        parent = optns.parent
        if parent and not 'CLAUSE' in parent.label:
            optns.label = optns.label.split('[')[0]
            clause_parent = find_node_in_upper_subtree(parent,'CLAUSE')
            if clause_parent:
                clause_parent.append(optns.detach())

    for auxtns in tree.subtrees(lambda n: 'AUX-TNS' in n.label):
        parent = auxtns.parent
        if parent and 'CORE' in parent.label and not sent[auxtns.leaves()[0]].lower() in ['will']:
            for x in parent:
                if x.label == 'NUC':
                    x.append(auxtns.detach())
        if (parent and 'CORE' in parent.label
                and sent[auxtns.leaves()[0]].lower() in ['will']):
            clause_parent = find_node_in_upper_subtree(parent, 'CLAUSE')
            if clause_parent:
                clause_parent.append(auxtns.detach())

    # easy repairs like op-neg
    for opneg in tree.subtrees(lambda n: 'OP-NEG' in n.label):
        parent = opneg.parent
        if parent and 'NP-PERI' in parent.label:
            pass
        elif parent and not 'CORE' in parent.label:
            opneg.label = opneg.label.split('[')[0]
            core_parent = find_node_in_upper_subtree(parent,'CORE')
            if core_parent:
                core_parent.append(opneg.detach())

    # easy repairs like op-def
    for opdef in tree.subtrees(lambda n: 'OP-DEF' in n.label):
        parent = opdef.parent
        if parent and not 'NP' in parent.label and not parent.label == 'NUC_Q':
            opdef.label = opdef.label.split('[')[0]
            np_parent = find_node_in_upper_subtree(parent,'NP')
            if np_parent:
                np_parent.append(opdef.detach())


    # put together two nucs which are not under nuc
    for nuc in tree.subtrees(lambda n: 'NUC' in n.label):

        two_idx = find_another_sibling_with_same_label(nuc, 'NUC')
        #print(two_idx)
        if two_idx and not (two_idx[1] - two_idx[0] < 2):
            #print('505')
            #print('403', nuc.parent[two_idx[0]])
            if not len(nuc.parent[two_idx[0]]) > 1:
                nuc.parent[two_idx[0]].append(nuc.parent[two_idx[1]].detach())
                nuc[1].prune() #!
                nuc.label = nuc.label.split('[')[0]

                if len(nuc) == 2 and "NUC" in nuc[1].label:
                    nuc[1].label = 'NUC???'
                    #nuc[0].spliceabove('NUC')

    # put together two nucs which are not under nuc
    for nucp in tree.subtrees(lambda n: 'NUC_P' in n.label):
        two_idx = find_another_sibling_with_same_label(nucp, 'NUC_P')
        if two_idx:# and not (two_idx[1] - two_idx[0] < 2):
            nucp.parent[two_idx[0]].append(nucp.parent[two_idx[1]].detach())
            nucp[1].prune() #!
            nucp.label = nucp.label.split('[')[0]

            if len(nucp) == 2 and "NUC_P" in nucp[1].label:
                nucp[1].label = 'NUC_P???'
                #nuc[0].spliceabove('NUC')

    # analogously, put together two cores which are not under core
    for core in tree.subtrees(lambda n: 'CORE' in n.label):
        two_idx = find_another_sibling_with_same_label(core, 'CORE')
        if two_idx and not (two_idx[1] - two_idx[0] < 2) \
                and not core.parent.label == 'CORE' \
                and not core.parent.label == 'CLAUSE':
            core.parent[two_idx[0]].append(core.parent[two_idx[1]].detach())
            core[1].prune()
            core.label = core.label.split('[')[0]

            if len(core) == 2 and "CORE" in core[1].label:
                core[1].label = 'CORE???'
                core[0].spliceabove('CORE')


    # if advp-peri is between two puncs, put it to the clause level
    for advpperi in tree.subtrees(lambda n: 'ADVP-PERI' in n.label):
        #if advpperi.parent.label in ['NUC']:#, 'NP']:
        #    if not advpperi.parent.parent.label == 'NP':
        #        advpperi.parent.parent.append(advpperi.detach())
        #if advpperi.parent.label == 'CORE_Q' and advpperi.parent.parent.parent.label == 'CORE_N':
        #    advpperi.parent.parent.parent.append(advpperi.detach())
        if len(advpperi) > 2 and sent[advpperi.leaves()[0]] in punc_list \
            and sent[advpperi.leaves()[-1]] in punc_list and advpperi.parent.label != 'NP':
            clause_parent = find_node_in_upper_subtree(advpperi.parent,'CLAUSE')
            if clause_parent:
                clause_parent.append(advpperi.detach())
        if (left_neighbour_word(advpperi, sent) in punc_list
                and right_neighbour_word(advpperi, sent) in punc_list):
            if advpperi.parent.parent and advpperi.parent.parent.label == 'CLAUSE':
                advpperi.label = advpperi.label.split('[')[0]
                advpperi.parent.parent.append(advpperi.detach())#
        elif sent[advpperi.leaves()[-1]].lower() in ['actually', 'perhaps', 'unexpectedly',
                                                      'course','probably','generally'#,'even','then',
                                                     'therefore', 'usually', 'really', 'certainly',
                                                     'obviously']\
                and advpperi.parent.label in ['CORE', 'CORE_N']:
            advpperi.parent.parent.append(advpperi.detach())
        elif (sent[advpperi.leaves()[-1]].lower() in ['almost', 'widely']
                and advpperi.parent.label == 'CORE'):  # and parent.parent.parent.parent.label == 'CORE'):
            for x in advpperi.parent:
                if x.label == 'NUC':
                    x.append(advpperi.detach())
    


    try:
        new_tree = postprocess(tree,sent)
        return new_tree, sent
    except:
        return tree, sent


def conv(tree, sent):

    # ensure there is a ROOT label, different from S
    #if tree.label != 'ROOT':
    #    tree = ParentedTree('ROOT', [tree])
    try:
        newtree, newsent = backtransform(tree, sent)
        removeemptynodes(newtree, newsent)
        return newtree
    except:
        removeemptynodes(tree, sent)
        return tree

#print(reader)

def readTreeFile(path_to_input_file):
    tb = reader(
        path_to_input_file,
        #functions='add',
        removeempty=True,
        #punct='add',
        morphology='no'# labels are of the form CAT-FUNC, store FUNC separately.
    )
    return tb

"""
out = open(output_file, 'w')

tb = readTreeFile(file_with_transformed_sents)

for n, (key, item) in enumerate(iter(tb.itertrees()),1):

    origtree = item.tree.copy(True).freeze()
    origsent = item.sent.copy()
    try:
        tree = conv(item.tree, item.sent)
        newtree = tree.copy(True).freeze()
        a = discodop_n.eval.bracketings(origtree)
        b = discodop_n.eval.bracketings(newtree)
        print('Converted tree:')
        print(DrawTree(newtree, origsent).text())
        if input_format.lower() in ['bracket', 'bracketed']:
            out.write(writediscbrackettree(tree, origsent, pretty=False))
        if input_format.lower() in ['negra', 'export']:
            out.write(writeexporttree(tree, origsent, key=key, comment=item.comment, morphology=None))
    except Exception as e:
        if input_format.lower() in ['bracket', 'bracketed']:
            out.write(writediscbrackettree(origtree, origsent, pretty=False))
        if input_format.lower() in ['negra', 'export']:
            out.write(writeexporttree(origtree, origsent, key=key, comment=item.comment, morphology=None))
        continue


out.close()
"""
