from pathlib import Path
import re
import torch
from scipy.special import softmax
import pandas as pd
import logging
import numpy as np
import sklearn
from collections import Counter
#from sklearn.metrics import accuracy_score 


def read_tsv(file_path):
    """
    Reads the data in

    Arguments:
    * data file path
    Returns:
    *sen_seq: a list of (sentence, corresponding supertags) pairs
    *sen_words: a list of sentences, 2 dim
    *sen_stags: a list of supertags, 2 dim
    """


    file_path = Path(file_path)

    raw_text = file_path.read_text().strip()
    raw_doc = re.split(r'\n\t?\n', raw_text)
    sen_seq = []
    sen_words = []
    sen_stags = []
    for doc in raw_doc:
        words = []
        stags = []

        for line in doc.split('\n'):
            _, word, _, supertags = line.split('\t')
            words.append(word)
            parts = supertags.split(":")
            stag = ':'.join(parts[:-1])
            stags.append(stag)
        sen_seq.append((words, stags))
        sen_words.append(words)
        sen_stags.append(stags)
      
    return sen_seq, sen_words, sen_stags

def data_prep(data_sequence):
    '''
    Preprocess data for creating DataFrame object
    Arguments:
    data_sequence: train_sequence/dev_sequence: tuples (sentence: [list of words], supertags: [list of corresponding supertags])
    return: list of lists of tuples: (sentence_id, word, supertag)
    '''
    data_list = []
    for (words, stags) in data_sequence:
        sentence_list = [] 
        for word, stag in zip(words, stags):
            sentence_list.append((word, stag))
        data_list.append(sentence_list)
    data = []

    for n in range(len(data_list)):
        for (word, stag) in data_list[n]:
            data.append([n, word, stag])
    return data

    
def encode_supertags(supertags):
    """
    Create the mappings for supertags 
    Arguments:
    *a list of all supertags
    Returns:
    *unique_supertags: a set of supertags
    *tag2id: dictionary {supertag:id}
    *id2tag: dictionary {id:supertag}
    """
    '''
    TODO: add tag2id and id2tag
    '''
    unique_supertags = set(stag  for seq in supertags for stag in seq)
    supertags_list = list(unique_supertags)
    tag2id = {label: id for id, label in enumerate(unique_supertags)}
    id2tag = {id: label for label, id in tag2id.items()}
    return supertags_list, tag2id, id2tag


def nbest_pred(model_outputs, id2tag, nbest):
    '''
    Returns the list of nbest predictions 
    Args:
    - list of model_outputs: for every word in a sentence a list of |dataset| predictions
    - id2tag mapping dict from id to supertag
    - number of best predictions to return
    returns: a list of lists, while the lists that represent sentences 
    contain the lists of nbest tuples (supertag, probability) for every word
        '''
    best_prediction_list = []
    for outputs in model_outputs:
        sentence_preds = []
        for output in outputs: 
            soft_out = list(softmax(np.mean(output, axis=0)))
            preds = (np.argsort(soft_out)[-nbest:]).tolist()
            best_preds = preds[::-1]
            best_probs = [soft_out[pred] for pred in best_preds]
            word_stags = []
            for pred, prob  in zip(best_preds, best_probs):
                supertag = id2tag[pred]
                tag = ":".join((supertag, str(prob)))
                word_stags.append(tag)
            sentence_preds.append(word_stags)
        best_prediction_list.append(sentence_preds)
    return best_prediction_list


def nbest_pred_soft(model_outputs, id2tag, nbest):
    '''
    -------------------------------------------------
    Function for .predict output after softmax layer
    -------------------------------------------------
    Returns the list of nbest predictions 
    Args:
    - list of model_outputs: for every word in a sentence a list of |dataset| predictions
    - id2tag mapping dict from id to supertag
    - number of best predictions to return
    returns: a list of lists, while the lists that represent sentences 
    contain the lists of nbest tuples (supertag, probability) for every word
        '''
    best_prediction_list = []
    for outputs in model_outputs:
        sentence_preds = []
        for output in outputs:
            #soft_out = list(softmax(np.mean(output, axis=0)))
            preds = (np.argsort(output)[-nbest:]).tolist()
            best_preds = preds[::-1]
            best_probs = [output[pred] for pred in best_preds]
            word_stags = []
            for pred, prob  in zip(best_preds, best_probs):
                supertag = id2tag[pred]
                tag = ":".join((supertag, str(prob)))
                word_stags.append(tag)
            sentence_preds.append(word_stags)
        best_prediction_list.append(sentence_preds)
    return best_prediction_list

def write_stag(nbest, sentences, file):
    '''
    creates the input file for partage: dev.supertag 
    with the nbest supertags predictied by the NERModel
    Args:
    - nbest the list of lists of tuples: (supertag:probability)
    - words: the list of sentences, every sentence is a list of words 
    Returns: 
    .supertag file: input for partage
    '''
    for (stags, sentence) in zip(nbest, sentences):
        for n, (word_stags, word) in enumerate(zip(stags, sentence)):
            #word_stags list of the supertags of a word
            file.write(str(n) + "\t" + word + "\t\t")
            for stag in word_stags:
                file.write(stag + "\t")
            file.write("\n")
        file.write("\n")
    file.close()
    return file

def write_pred(pred, sentences, file):
    '''
    creates the file for calculating accuracy: predicted.supertag 
    Args:
    - nbest the list of lists of tuples: (supertag:probability)
    - words: the list of sentences, every sentence is a list of words 
    Returns: 
    .supertag file: input for partage
    '''
    for (stags, sentence) in zip(pred, sentences):
        for n, (word_stags, word) in enumerate(zip(stags, sentence)):
            #word_stags list of the supertags of a word
            file.write(str(n) + "\t" + word + "\t\t")
            file.write(word_stags + "\t")
            file.write("\n")
        file.write("\n")
    file.close()
    return file

def stag_compare(predictions, supertags, sentences, file):
    '''
    creates the input file for partage: dev.supertag 
    with the nbest supertags predictied by the NERModel
    Args:
    - nbest the list of lists of tuples: (supertag:probability)
    - words: the list of sentences, every sentence is a list of words 
    Returns: 
    .supertag file: input for partage
    '''
    for (sentence, stags, preds) in zip(sentences, supertags, predictions):
        for n, (word, stag, pred) in enumerate(zip(sentence, stags, preds)):
            #word_stags list of the supertags of a word
            file.write(str(n) + "\t" + word + "\t" + stag + "\t" + pred)
            file.write("\n")
        file.write("\n")
    file.close()
    return file


def accuracy(predictions, supertags):
    '''
    calculate the accuracy of the model
    Args:
    - list of predictions (list of lists)
    - list of supertags (list of lists)
    Returns:
    accuracy
    '''
    correct, total = 0, 0
    for preds, stags in zip(predictions, supertags):
        for pred, stag in zip(preds, stags):
            if stag == pred:
                correct += 1
        total += len(stags)

    return float(correct)/total



def punct(predictions, sentences, supertags):
    '''
    discard punctuation predictions and supertags
    args:
    predictions: list of predictions
    senteces: list of sentences
    supertags: list og gold supertags
    returns:
    list of predictions and list of supertags without punctuation
    '''
    punct = ["'", ".", ",", "(", ")", ":", "-", ";", "?", "/", "!", "*", "&", "`", "[", "]", "<", ">", "\""]    
    new_pred = []
    new_test = []
    new_stags = []
    for preds, sent, stags in zip(predictions, sentences, supertags):
        preds_list = []
        words = []
        stag_list = []
        for pred, word, stag in zip(preds, sent, stags):
            if any(p == word for p in punct):
                pass
            else:
                preds_list.append(pred)
                words.append(word)
                stag_list.append(stag)
        new_pred.append(preds_list)
        new_test.append(words)
        new_stags.append(stag_list)
    return new_pred, new_stags, new_test


def accuracy_1(predictions, supertags, sentences, punct):
    
    '''
    TODO: add list of words
    calculate the accuracy of the model doesn't count the accuracy of the punctuation
    Args:
    - list of predictions (list of lists)
    - list of supertags (list of lists)
    - sentences: list of sentences (list of lists)
    - punct: list of punctuation marks to ignore while calculating accuracy
    Returns:
    accuracy of the model, whiwhout counting accuracy of predictions made on punctuation
    '''
    correct, total, tot = 0, 0, 0
    for preds, stags, sents in zip(predictions, supertags, sentences):
        for (pred, stag, word) in zip(preds, stags, sents):
            if ("'" != word) or ("." != word) or ("," != word) or ("(" != word) or (")" != word) or (":" != word) or ("-" != word) or (";" != word) or ("?" != word) or ("/" != word) or ("!" != word) or ("*" != word) or ("&" != word) or ("`" != word) or ("[" != word) or ("]" != word) or ("<" != word) or (">" != word) or ("\"" != word):
                tot += 1
                if stag == pred:
                    correct += 1
        total += tot

    return float(correct)/total

def error_count(supertags, predictions):
    '''
    returns the coount of wrong predicted supertags and two lists with supertags 
    from most common to less common and their counts respectively
    args: gold supertags, predictions
    return: error list  from most to less common
        erroneous supertags list  from most to less common
        count list of incorrect predicted supertags
    '''
    errors = Counter()
    for pred, gold in zip(supertags, predictions):
        for elem1, elem2 in zip(pred, gold):

            if elem1 != elem2:
                errors[elem1] += 1
    sups = []
    counts = []
    for (sup,count) in errors.most_common():
        sups.append(sup)
        counts.append(count)
    return errors, sups, counts



