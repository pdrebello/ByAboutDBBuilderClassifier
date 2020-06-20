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
resolved_entity_table = 'entities_resolved_overall'
article_table = 'aadhar'
by_about_table = 'by_about'
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
by_about_table = db["by_about"] # collection we will construct to hold By/About statements

#lis = by_about_table.aggregate([{$group : {_id : "$type"}}])


#pipeline = [{$group : {_id : "$type"}}]
pipeline = [{"$group" : {"_id" : "$stdName", "type" : { "$first": '$type' }}}]
cursor = list(collection.aggregate(pipeline, allowDiskUse=True))

import pickle

dic = {}
for i in cursor:
    dic[i['_id']] = i['type']
file_pi = open('stdName_to_type.obj', 'wb') 
pickle.dump(dic, file_pi)
