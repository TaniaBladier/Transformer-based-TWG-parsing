

import torch
from scipy.special import softmax
import numpy as np
from simpletransformers.ner import NERModel
from utils import nbest_pred
import json
import subprocess
import sys, os
sys.path.insert(1, '/transformers')
from discodop_n.treebank import incrementaltreereader, writediscbrackettree, writeexporttree
from discodop_n.tree import DrawTree, ParentedTree, Tree
import time
from backtransformation import conv

import argparse

arg_parser = argparse.ArgumentParser(description = __doc__)
arg_parser.add_argument('input_file')
arg_parser.add_argument('output_file')

args = arg_parser.parse_args()

inp_file = args.input_file

outfile  = open(args.output_file, 'w')

def invert_dict(index_dict):
    return {j:i for i,j in list(index_dict.items())}

def load_t2supertag(stag_dict_json_file):
    json1_file = open(stag_dict_json_file)
    json1_str = json1_file.read()
    json1_data = json.loads(json1_str)

    return json1_data

def nbest_pred(model_outputs, id2tagxlnet, nbest):

    best_prediction_list = []
    for outputs in model_outputs:
        sentence_preds = []
        for output in outputs:
            #print()
            #print(output)
            #print()
            soft_out = list(softmax(np.mean(output, axis=0)))
            #print(soft_out)
            preds = (np.argsort(soft_out)[-nbest:]).tolist()
            #print(preds)
            best_preds = preds[::-1]
            best_probs = [soft_out[pred] for pred in best_preds]
            word_stags = []
            for pred, prob  in zip(best_preds, best_probs):
                supertag = id2tagxlnet[pred]
                tag = ":".join((supertag, str(prob)))
                word_stags.append(tag)
            sentence_preds.append(word_stags)
        best_prediction_list.append(sentence_preds)
    return best_prediction_list


def string_for_partage(nbest, sentences):
    line_for_partage = ''
    for (stags, sentence) in zip(nbest, sentences):
        for n, (word_stags, word) in enumerate(zip(stags, sentence)):
            stag_list = '\t'.join(word_stags)
            line_for_partage = line_for_partage + str(n +1) + "\t" + word + "\t\t" + stag_list +'\n'
        line_for_partage = line_for_partage +'\n'
    return line_for_partage.strip()



device = torch.cuda.is_available()

language_model = NERModel(
    "bert", "best_model", use_cuda=device # for French, replace "bert" with "camembert"
)

labels = language_model.args.labels_list
id2tagxlnet = {id:label for id, label in enumerate(labels)}

def get_nbest_output_for_partage(sentences, modelname):
    predictions, raw_output = modelname.predict(sentences, split_on_space=False)

    best_predictions = nbest_pred([[[v[0] for k,v in p.items()] for p in x] for x in raw_output], id2tagxlnet, 15)


    str_for_partage = string_for_partage(best_predictions, sentences)
    return str_for_partage

def partage_parse_supertag_file(filepath):
    pparses_bracketed = []
    pparses_supertags = []
    try:
        produce_bracketed = 'partage-twg astar -i stags_for.partage' \
            ' -s "s SENTENCE NP PP TEXT AP ADVP QP' \
            ' CORE FRAG CLAUSE NP-WH NP-REL" ' \
            '-t 15 -d 0 --print-parses 1 -v 0 -p'
        produce_supertagged = 'partage-twg astar -i stags_for.partage' \
            ' -s "s SENTENCE NP PP TEXT AP ADVP QP' \
            ' CORE FRAG CLAUSE NP-WH NP-REL" ' \
            '-t 15 -d 0 --print-parses 1 -v 0'
        output_bracketed = subprocess.check_output(
            produce_bracketed, shell=True).decode('UTF-8')
        output_supertags = subprocess.check_output(
            produce_supertagged, shell=True).decode('UTF-8')
        output_bracketed = [s for s in output_bracketed.split('\n') if len(s) > 0]
        pparses_supertags.append(output_supertags.strip())
        for par in output_bracketed:
            par = par.strip()

            if par.startswith('('):
                try:
                    for t, s, comment in incrementaltreereader(par.strip()):
                        output_backtransformed = conv(t, s)
                        if output_backtransformed:
                            pparses_bracketed.append(writediscbrackettree(
                            output_backtransformed, s))
                        else:
                            pparses_bracketed.append('kkl' + writediscbrackettree(
                            t, s))
                except:     
                    #pparses_bracketed.append('ere\n')
                    #pparses_supertags.append("NO PARSE")
                    pass
            else:
                pparses_bracketed.append(par.strip() + '\n')

    except:
        pparses_bracketed.append("NO PARSE\n")
        pparses_supertags.append("NO PARSE\n")
        pass
    
    cur_path = os.getcwd()

    if os.path.exists(cur_path + "/" + filepath):
        os.remove(cur_path + "/" + filepath)

    return pparses_bracketed, pparses_supertags


def xlnetsupertagging_en(sentences):
    
    tmpfilepath = 'stags_for.partage'
    output_for_partage = get_nbest_output_for_partage(sentences, language_model)

    with open(tmpfilepath, 'w') as outf:
        outf.write(output_for_partage)
        outf.close()

    pparses_bracketed, pparses_supertags = partage_parse_supertag_file(tmpfilepath)
    return pparses_bracketed, pparses_supertags


#######################

with open(inp_file, "r") as inf:
    for line in inf:
        sent = line.replace("(", '-LRB-').replace(")", "-RRB-").strip().split(" ")
        pp_br, pp_st = xlnetsupertagging_en([sent])
        for x in pp_br:
            x = x.strip()
            try:
                for t, s, c in incrementaltreereader(x):
                    l = len(t.leaves())
                    if len(sent) == l:
                        outfile.write("\n".join(pp_st).replace("-LRB-", "(").replace("-RRB-", ")") + "\n")
                        outfile.write(x + '\n\n')
                    else:
                        pass
                        #outfile.write('WRONG LEAVES: ' + line + '\n')
            except:
                pass

            
outfile.close()
