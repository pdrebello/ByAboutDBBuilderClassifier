from stanfordcorenlp import StanfordCoreNLP
from datetime import datetime
import json
import re, string, os, itertools
import nltk
from nltk.corpus import stopwords
from collections import defaultdict
import os
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import subprocess
import shlex
from pymongo import MongoClient
import pathlib
from ExtractSentences import ExtractSentences
from text_parser import StanfordNLP

fixed_keywords = ['says', 'said', 'asks', 'asked', 'told', 'announced', 'announce', 'claimed', 'claim']

def get_all_entities(collection, types, num_entities=-1):
    '''
    Method to parse all the entities from the collection of a particular 'type'
    '''
    pipeline = [{"$project":{"stdName":1,"type":1,"aliases":1,"articleIds":1,"num":{"$size":"$articleIds"}}}]
    cursor = list(collection.aggregate(pipeline))
    top_n_entities = {}
    entities = {type:[] for type in types}
    for ent in cursor:
        if(ent['type'] in types):
            entities[ent['type']].append(ent)

    for type in entities.keys():
        entities[type].sort(key=lambda x: x['num'], reverse=True)
        if num_entities == -1:
            num_entities = len(entities[type])
            print('All the {} entities are under consideration.'.format(num_entities))
        else:
            print('Num of top-entities under consideration: {}'.format(num_entities))
        top_n_entities[type] = [{"name":obj['stdName'],"coverage":obj['num'],"aliases":obj['aliases'],"articleIds":obj['articleIds']} for obj in entities[type][:num_entities]]
    return top_n_entities

def findSentiment(sentiString):
    '''
    return Sentiment by Vader
    :param sentiString:
    :return:
    '''
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(sentiString)
    a_sent = (sentiment["compound"])
    return a_sent

'''
entitySpecificSentimentAnalysis:
    takes two argument
    1. Input File : set of sentences
    2. Keywords associated with target

    and output two list
    1. Articles on target
    2. Articles by target
    3. Articles not about target
'''


def preprocesstext(doc_set):
    text = doc_set.lower()
    text = text.replace('\r', '')
    text = text.replace('\r\n', '')
    text = text.replace('\n', '')
    text = text.replace('"', '')
    text = text.replace('%', ' ')
    return text


def entitySpecificCoverageAnalysis(sentence, entity_keywords, entity_name, e_aliases):
    
    sNLP = StanfordNLP()
    onTargetArticles = []
    byTargetArticles = []
    removedArticles = []
    short_entity_name = ''.join(entity_name.split()).lower()
    entity_keywords.append(short_entity_name)
    
    text = preprocesstext(sentence)
    
    for alis in e_aliases:
        text = text.replace(alis.lower() + ' ', short_entity_name + ' ')
        text = text.replace(alis.lower() + '. ', short_entity_name + ' . ')
        text = text.replace(alis.lower() + ', ', short_entity_name + ' , ')
    
    try:
        pos_text = sNLP.pos(text)
    except json.decoder.JSONDecodeError:
        print('JSON_Decode_Error: ', text)
        return
    parse_text = sNLP.dependency_parse(text)
    state1 = False
    state2 = False
    
    for pt in parse_text:
        print(pos_text[pt[1] - 1][0])
        print(pos_text[pt[2] - 1][0])
        if ((pt[0] == 'nsubj') or (pt[0] == 'nmod') or (pt[0] == 'amod') or (pt[0] == 'dobj')) and (
                    (pos_text[pt[1] - 1][0] in entity_keywords) or (pos_text[pt[2] - 1][0] in entity_keywords)):
            if ((pt[0] == 'nsubj') and (
                            pos_text[pt[1] - 1][0] in fixed_keywords or pos_text[pt[2] - 1][0] in fixed_keywords)):
                state2 = True
                #action is the by keyword e.g "says", "said", "told" etc
                if(pos_text[pt[1] - 1][0] in fixed_keywords):
                    action = pos_text[pt[1] - 1][0]
                else:
                    action = pos_text[pt[2] - 1][0]
            else:
                state1 = True
    #if a By statement    
    if(state2):
        ccomp = False
        for pt in parse_text:
            #Find ccomp, and one of the words = action
            if(pt[0] == 'ccomp'):
                if((pos_text[pt[1] - 1][0] == action)):
                    ccomp = True
                    complement = pos_text[pt[2] - 1][0]
                if((pos_text[pt[2] - 1][0] == action)):
                    ccomp = True
                    complement = pos_text[pt[1] - 1][0]
        #if ccomp condition is true, find who or what is being spoken about
        if(ccomp):
            for pt in parse_text:
                if(pt[0] == 'nsubj'):
                    if((pos_text[pt[1] - 1][0] == complement)):
                        talking_about = pos_text[pt[2] - 1][0]
                        print("Talking About: " + talking_about)
                    if((pos_text[pt[2] - 1][0] == complement)):
                        talking_about = pos_text[pt[1] - 1][0]
                        print("Talking About: " + talking_about)
    print(sentence + "\n" + str(state1) + " " + str(state2) + " \n")

