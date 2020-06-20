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
from utils import *
from print_methods import *
from ExtractSentences import ExtractSentences
from text_parser import StanfordNLP
import config, sys, argparse

# disable proxy
os.environ['no_proxy'] = '*'

# Initialise the article collection set and set of resolved entities
resolved_entity_table = config.resolved_entity_table
article_table = config.article_table
by_about_table = config.by_about_table

parser = argparse.ArgumentParser(description='Extract by/about statements',
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                )
parser.add_argument('--name', nargs='?', help='name of the entity')
parser.add_argument('--names_path', nargs='?', help='path name for all entity names')
parser.add_argument('--folder', nargs='?', help='folder name to dump files to')
parser.add_argument('--start', type=int, default=0, help='start index')
parser.add_argument('--end', type=int, default=9, help='end index')
parser.add_argument('--aliases_path', nargs='?', help='path name for corresponding aliases')
parser.add_argument('--N', type=int, default=-1, help='name of the entity')
args = parser.parse_args()
# Establish connection with media-db
client = MongoClient(config.mongoConfigs['host'], config.mongoConfigs['port'])
db = client[config.mongoConfigs['db']]
collection = db[resolved_entity_table]  # collection having resolved entities
art_collection = db[article_table]  # collection having articles
by_about_table = db[by_about_table] # collection we will construct to hold By/About statements
print('Connection established with the server. Make sure that your StanfordCoreNLP is also running.')

# globals
entity_types = config.entity_types
short_sources_list = config.short_sources_list
sources_list = config.sources_list

# get the list of all entities
#entities = get_all_entities(collection, entity_types, args.N)
print('All resolved entities crawled from the database')



# object for extracting sentences from text
extractor = ExtractSentences()  

#prepare a dictionary to convert entity to it's type - person, company etc 
pipeline = [{"$group" : {"_id" : "$stdName", "type" : { "$first": '$type' }}}]
cursor = list(collection.aggregate(pipeline, allowDiskUse=True))

entity_type_dic = {}
for i in cursor:
    entity_type_dic[i['_id']] = i['type']

#Get all entities from the entity table
e_names = []
e_aliases = []
e_articleIds = []

for type in entities.keys():
    seen = {}
    for i,entity in enumerate(entities[type]):
        if(entity['name'] in seen):
            
            if(seen[entity['name']][0] < len(entity["articleIds"])):
                seen[entity['name']] = (len(entity["articleIds"]),i)
        else:
            seen[entity['name']] = (len(entity["articleIds"]),i)
    for k in seen.keys():
        e_names.append(entities[type][seen[k][1]]['name'])
        e_aliases.append(entities[type][seen[k][1]]['aliases'])
        e_articleIds.append(entities[type][seen[k][1]]["articleIds"])


#Insert Sentences into the by-about database. Do this by scanning entities.
print("Number of Entities Scanning: " + str(len(e_names)))
for i in range(len(e_names)):
    print("Processing Entity: " + str(i) +"/"+str(len(e_names)),end="\r")
    articles = {s: [] for s in sources_list}
    new_entity_alias = []

    new_entity_alias.extend(e_aliases[i])
    
    for article_id in e_articleIds[i]:
        try:
            article = art_collection.find({"_id": article_id})[0]
        except:
            continue
        # url = article["articleUrl"]
        text = article["text"]
        source = article["sourceName"]
        #print(source, ' , #articles : ', len(articles[source]))
        sentences = []
        sentences = extractor.split_into_sentences(str(text))
        
        aliases = new_entity_alias
        
        temp = entitySpecificCoverageAnalysis(sentences, aliases, e_names[i], new_entity_alias)
        (onTargetArticles) = temp[0] 
        (byTargetArticles) = temp[1] 
        (removedArticles) = temp[2]
        
        documents = []
        for l in onTargetArticles:
            #Do an update if the sentence already exists in database
            temp = by_about_table.find({'Sentence':l[0]})
            
            if(temp.count()>0):
                if('About' in temp):
                    about = temp['About']
                    about.append(e_names[i])
                    by_about_table.update(
                    { 'Sentence': l[0] },
                    { '$set': { 'About': about } },
                    upsert=False
                    )
                else:
                    by_about_table.update(
                    { 'Sentence': l[0] },
                    { '$set': { 'About': [e_names[i]] } },
                    upsert=False
                    )
                continue
            
            #Create a fresh document if sentence doesn't exist in database
            document = {}
            document['Sentence'] = l[0]
            document['Location'] = l[1]
            document['Previous Sentence'] = l[2]
            document['Next Sentence'] = l[3]
            document['ArticleID'] = article_id
            document['About'] = [e_names[i]]
            document['Source'] = source
            
            by_about_table.insert_one(document)
            
        for l in byTargetArticles:
            #Do an update if the sentence already exists in database
            temp = by_about_table.find({'Sentence':l[0]})
            
            if(temp.count()>0):
                if('By' in temp):
                    by = temp['By']
                    by.append(e_names[i])
                    by_about_table.update(
                    { 'Sentence': l[0] },
                    { '$set': { 'By': by } },
                    upsert=False
                    )
                else:
                    by_about_table.update(
                    { 'Sentence': l[0] },
                    { '$set': { 'By': [e_names[i]] } },
                    upsert=False
                    )
                continue
            #Create a fresh document if sentence doesn't exist in database
            document = {}
            document['Sentence'] = l[0]
            document['Location'] = l[1]
            document['Previous Sentence'] = l[2]
            document['Next Sentence'] = l[3]
            document['ArticleID'] = article_id
            document['By'] = [e_names[i]]
            document['Source'] = source
            by_about_table.insert_one(document)

#Classify the Sentences in the database into on eof 6 classes
classify(by_about_table,entity_type_dic)
class5(by_about_table)

#Optional Print The Database into a CSV
#printAll(by_about_table)



