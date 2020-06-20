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
from improvedAboutChecker import *
import csv

fixed_keywords = ['says', 'said', 'asks', 'asked', 'told', 'announced', 'announce', 'claimed', 'claim', "explained","states","stated","declared","declares","added"]

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


def entitySpecificCoverageAnalysis(doc_set, entity_keywords, entity_name, e_aliases):
    '''
    Finds the sentences that are about or by the entity
    :param doc_set: set of sentences
    :param entity_keywords: keywords as to which entity to identify in the sentence.
    :return: onTarget_sentences, byTarget_sentences, removed_sentences, onTargetTopic, byTargetTopic
    '''
    #f= open("missed_aadhar.txt","w")
    sNLP = StanfordNLP()
    onTargetArticles = []
    byTargetArticles = []
    removedArticles = []
    short_entity_name = ''.join(entity_name.split()).lower()
    entity_keywords.append(short_entity_name)
    for i in range(len(doc_set)):
        #print('Document: {}'.format(i))
        text = preprocesstext(doc_set[i])
        for alis in e_aliases:
            text = text.replace(alis.lower() + ' ', short_entity_name + ' ')
            text = text.replace(alis.lower() + '. ', short_entity_name + ' . ')
            text = text.replace(alis.lower() + ', ', short_entity_name + ' , ')
        
        try:
            pos_text = sNLP.pos(text)
        except json.decoder.JSONDecodeError:
            print('JSON_Decode_Error: ', text)
            continue
        parse_text = sNLP.dependency_parse(text)
        state1 = False
        state2 = False
        
        for pt in parse_text:
            #print(pt)
            #print(pos_text[pt[1] - 1][0])
            #print(pos_text[pt[2] - 1][0])
            #(pt[0] == 'nmod') or (pt[0] == 'amod') or 
            if ((pt[0] == 'nmod') or (pt[0] == 'amod')):
                mod = "NULL"
                if(pos_text[pt[1] - 1][0] in entity_keywords):
                    mod = pos_text[pt[2] - 1][0]
                if(pos_text[pt[2] - 1][0] in entity_keywords):
                    mod = pos_text[pt[1] - 1][0]
                if(mod != "NULL"):
                    for pt in parse_text:
                        if ((pt[0] == 'nsubj') or (pt[0] == 'dobj')):
                            if(pos_text[pt[1] - 1][0] == mod):
                                if(pos_text[pt[2] - 1][0] in fixed_keywords):
                                    state2 = True
                            if(pos_text[pt[2] - 1][0] == mod):
                                if(pos_text[pt[1] - 1][0] in fixed_keywords):
                                    state2 = True
                else:
                    if(pos_text[pt[1] - 1][0] in entity_keywords):
                        state1 = True
                    if(pos_text[pt[2] - 1][0] in entity_keywords):
                        state1 = True
            #He told tom, sam, harry and jack            
            if((pt[0] == 'conj')):
                compound = "NULL"
                if(pos_text[pt[1] - 1][0] in entity_keywords):
                    compound =  pos_text[pt[2] - 1][0]
                if(pos_text[pt[2] - 1][0] in entity_keywords):
                    compound =  pos_text[pt[1] - 1][0]
                    
                if(compound != "NULL"):
                    for pt in parse_text:
                        if ((pt[0] == 'dobj') or (pt[0] == 'cop')):
                            if(pos_text[pt[1] - 1][0] == compound):
                                state1 = True
                            if(pos_text[pt[2] - 1][0] == compound):
                                state1 = True
                        if (pt[0] == 'nsubj'):
                            if((pos_text[pt[1] - 1][0] == compound) and (pos_text[pt[2] - 1][0] in fixed_keywords)):
                                state2 = True
                            if((pos_text[pt[2] - 1][0] == compound) and (pos_text[pt[1] - 1][0] in fixed_keywords)):
                                state2 = True
                
                        
                        
            if ((pt[0] == 'nsubjpass') or (pt[0] == 'nsubj') or (pt[0] == 'dobj')) and (
                        (pos_text[pt[1] - 1][0] in entity_keywords) or (pos_text[pt[2] - 1][0] in entity_keywords)):
                
                if (((pt[0] == 'nsubj')or(pt[0] == 'nsubjpass')) and (
                                pos_text[pt[1] - 1][0] in fixed_keywords or pos_text[pt[2] - 1][0] in fixed_keywords)):
                    state2 = True
                elif ((pt[0] == 'dobj') and (
                                pos_text[pt[1] - 1][0] in fixed_keywords or pos_text[pt[2] - 1][0] in fixed_keywords)):
                    state2 = True
                else:
                    #print(pt)
                    #print(pos_text[pt[1] - 1][0])
                    #print(pos_text[pt[2] - 1][0])
                    state1 = True
        
        if (i>0): 
            prev = doc_set[i-1] 
        else:
            prev = "-"
        if (i<len(doc_set)-1): 
            nex = doc_set[i+1] 
        else:
            nex = "-"
            
        if state1:
            onTargetArticles.append((doc_set[i],i,prev,nex))
        if state2:
            byTargetArticles.append((doc_set[i],i,prev,nex))

        
        if(not(state1) and not(state2)):
            #print which sentecnes with the entities are missed
            #if(short_entity_name in text):
                #print(text)
                #print(short_entity_name)
                #print("\n")
                #f.write(text)
                #f.write("\n")
                #f.write(short_entity_name)
                #f.write("\n\n")
            removedArticles.append((doc_set[i],i))
    #f.close()
    
    return (onTargetArticles, byTargetArticles, removedArticles)

def get_names_aliases_articles(entities):
    e_names = []
    e_aliases = []
    e_articleIds = []
    indices = []
    for type in entities.keys():
        for entity in entities[type]:
            e_names.append(entity['name'])
            e_aliases.append(entity['aliases'])
            e_articleIds.append(entity["articleIds"])
    return (e_names, e_aliases, e_articleIds)

def findPowerEliteIndex(entity_name, e_names, e_aliases):
    '''
    FInd all the entity resolution which may contain the given entity.
    :param entity_name: Given entity
    :param e_names: list of all entity names
    :param e_aliases: list of all entity aliases
    :return: set of indices
    '''
    print('Search ', entity_name, ' : ', len(e_names))
    indices = []
    for i in range(len(e_names)):
        name = e_names[i].replace('.', '')
        alias = ','.join(e_aliases[i])
        if entity_name.lower() in name.lower() or entity_name.lower() in alias.lower():
            indices.append(i)
    return indices

#print the by about table into CSV format
def printAll(collection):
    
    f1 = open("class1.csv","w", newline='')
    f3 = open("class3.csv","w", newline='')
    f5 = open("class5.csv","w", newline='')
    f6 = open("class6.csv","w", newline='')
    writer1 = csv.writer(f1)
    writer3 = csv.writer(f3)
    writer5 = csv.writer(f5)
    writer6 = csv.writer(f6)
    for i in collection.find():
        if('Class' in i):
            clas = i['Class']
            if(clas == '1'):
                writer1.writerow([i['Sentence'],"No By", i['About']])
            if(clas == '3'):
                writer3.writerow([i['Sentence'],i['By'], i['About']])
            if(clas == '5'):
                writer5.writerow([i['Sentence'],i['By'], i['About']])
            if(clas == '6'):
                writer6.writerow([i['Sentence'],"No By", "No About"])
    f1.close()
    f3.close()
    f5.close()
    f6.close()

#analyse class5 statements to pick out what is being talked about
def class5(collection):
    sNLP = StanfordNLP()
    for i in collection.find():
        try:
            clas = i['Class']
        except:
            continue  
        if(int(clas) == 5):
            about = getabout(i['Sentence'],sNLP)
            collection.update(
                    { 'Sentence': i['Sentence'] },
                    { '$set': { 'About': about } },
                    upsert=False
                    )
        
import pickle

#classify by-about statements into a class: arguments are: ByAboutTable, A dictionary converting entity to type 
def classify(collection,stdName_to_type):
    
    for i in collection.find():
        if('By' in i):
            By = i['By']
        else:
            By = 'No By'
        if('About' in i):
            About = i['About']
        else:
            About = 'No About'
        
        if(By == "No By"):
            type = stdName_to_type[About[0]]
            if(type == 'Person'):
                classs = 1
            else:
                classs = 2
        else:
            if(About == 'No About'):
                classs = 5
            else:
                type = stdName_to_type[About[0]]
                if(type == 'Person'):
                    classs = 3
                else:
                    classs = 4
                    
        collection.update(
                        { 'Sentence': i['Sentence'] },
                        { '$set': { 'Class': classs } },
                        upsert=False
                        )
