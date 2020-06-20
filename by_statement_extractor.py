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
article_table = 'articles'

# Choose the name of entity to run
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

# Deciding which folder to dump files to
if args.name is not None:
    folder = 'others'
else:
    if args.folder is None:
        print('Please specify the folder name to dump files to.\nExiting...')
        exit()
    folder = args.folder

# Printing the entity name if specified
if args.name is not None:
    print('Entity Name to get the by & about statements for : {}'.format(args.name))

# Displaying the number of entites under consideration (-1 denotes all the entities)
if args.N < 0:
    print('All the entities in the database are under consideration.')
else:
    print('Search for by-statements ONLY in the top-{} entities'.format(args.N))

if args.names_path is not None:
    print('Current domain: {}'.format(folder))

# Establish connection with media-db
client = MongoClient(config.mongoConfigs['host'], config.mongoConfigs['port'])
db = client[config.mongoConfigs['db']]
collection = db[resolved_entity_table]  # collection having resolved entities
art_collection = db[article_table]  # collection having articles
print('Connection established with the server. Make sure that your StanfordCoreNLP is also running.')

# globals
entity_types = config.entity_types
short_sources_list = config.short_sources_list
sources_list = config.sources_list

# get the list of all entities
entities = get_all_entities(collection, entity_types, args.N)
print('All resolved entities crawled from the database')

# parse entities list to get names, aliases and articles
e_names, e_aliases, e_articleIds = get_names_aliases_articles(entities)
print('e_names, e_aliases & e_articleIds parsed from entities list')

# object for extracting sentences from text
extractor = ExtractSentences()  

def statements_per_entity(entity_name, aliases=None):

    # Output folder
    res_folder = './Outputs/' + folder + '/' + entity_name + '/'
    directory = os.path.dirname(res_folder)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # search for entity name and get all occurences
    entity_ind = findPowerEliteIndex(entity_name, e_names, e_aliases)
    print('Occurences in entities set : {}'.format(entity_ind))

    # filter articles as per the article ids and source
    articles = {s: [] for s in sources_list}
    print(entity_name + ' : READ ARTICLE IDS ...')
    new_entity_alias = []
    for l in range(len(entity_ind)):
        new_entity_alias.extend(e_aliases[entity_ind[l]])
        for article_id in e_articleIds[entity_ind[l]]:
            article = art_collection.find({"_id": article_id})[0]
            # url = article["articleUrl"]
            text = article["text"]
            source = article["sourceName"]
            if source in sources_list:
                articles[source].append(text)
    print('Articles filtered as per the source category.\nNumber of aliases found: {}'.format(len(new_entity_alias)))

    # get by & about statements and dump them into the output folder
    for j in range(1, len(sources_list)):
        source = sources_list[j]
        print(source, ' , #articles : ', len(articles[source]))
        sentences = []

        print('Extract sentences...')
        for text in list(set(articles[source])):
            ext_sentences = extractor.split_into_sentences(str(text))
            sentences.extend(ext_sentences)

        print('Find entity specific sentences...')
        if aliases is None:
            aliases = new_entity_alias
        onTargetArticles, byTargetArticles, removedArticles = entitySpecificCoverageAnalysis \
            (sentences, aliases, entity_name, new_entity_alias)

        print('Print about and by entity sentences to file...')
        about_sent, by_sent = printToFile(res_folder, onTargetArticles, byTargetArticles,
                                        entity_name, short_sources_list[j])
        printRemovedToFile(res_folder, entity_name, short_sources_list[j], removedArticles)

        print(entity_name, source, "done...")
        print('About: ', len(onTargetArticles), ' By: ', len(byTargetArticles), 'Removed: ', len(removedArticles))
        print('About: ', about_sent, ' By: ', by_sent, '\n')

    print('All By & About Statements Dumped for {}'.format(entity_name))
    return

def statements_for_top_n_entities():
    if args.names_path is None:
        print('Please specify the file containing the list of all entity names.\nExiting...')
        exit()
    
    aliases_path = args.aliases_path
    aliases = None
    if aliases_path is not None:
        fwrite_temp = open(aliases_path, 'r')
        aliases = [list(map(str.lower, map(str.strip, line.split(",")))) for line in fwrite_temp]
        print("Read all aliases of all entities...")

    names_path = args.names_path
    power_elitesdata = np.genfromtxt(names_path, delimiter='\t', dtype=str)
    power_elites = power_elitesdata[:, 0]
    print("Read all power elite names...")

    start_ind = args.start
    end_ind = args.end
    print("start index: ", start_ind, "  end index:", end_ind)
    for i in range(start_ind, end_ind + 1):
        print('Running for the {}-th entity'.format(i))
        entity_name = power_elites[i]
        if aliases is not None:
            statements_per_entity(entity_name, aliases[i])
        else:
            statements_per_entity(entity_name)
    return

if args.name is not None:
    statements_per_entity(args.name)
else:
    statements_for_top_n_entities()
    

