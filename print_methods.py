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

#def returnDocument(res_folder, about_entity, by_entity, entity, source):

def printToFile(res_folder, about_entity, by_entity, entity, source):
    about_sent = 0
    by_sent = 0
    documents = []
    """
    if len(about_entity):
        for l in range(len(about_entity)):
            line = about_entity[l]
            line_sent = findSentiment(line)
            document = {}
            document['entityID'] = 
            document['EntityName'] = 
            document['ArticleID'] = 
            document['Statement'] = 
            document['ByOrAbout'] = 
            document['Location'] = 
            document['Sentiment'] = 
            document['Source'] = 
            outfile.write(';;' + str(line_sent) + ';;' + line + '\n')
            about_sent = about_sent + line_sent
        outfile.close()
    """
    if len(by_entity):
        fname = './' + res_folder + '/by_' + '_'.join(entity.split()) + '_' + source + '.txt'
        outfile = open(fname, 'w')
        for l in range(len(by_entity)):
            line = by_entity[l]
            line_sent = findSentiment(line)
            outfile.write(';;' + str(line_sent) + ';;' + line + '\n')
            by_sent = by_sent + line_sent
        outfile.close()
    return (about_sent, by_sent)
    '''
    :param about_entity: set of sentences that are about the entity
    :param by_entity:  set of sentences that are statements made by the entity
    :param entity: Entity name
    :param source: News source Short URL to be used in file naming
    :return: None
    '''
    about_sent = 0
    by_sent = 0
    if len(about_entity):
        fname = './' + res_folder + '/about_' + '_'.join(entity.split()) + '_' + source + '.txt'
        outfile = open(fname, 'w')
        for l in range(len(about_entity)):
            line = about_entity[l]
            line_sent = findSentiment(line)
            outfile.write(';;' + str(line_sent) + ';;' + line + '\n')
            about_sent = about_sent + line_sent
        outfile.close()
    if len(by_entity):
        fname = './' + res_folder + '/by_' + '_'.join(entity.split()) + '_' + source + '.txt'
        outfile = open(fname, 'w')
        for l in range(len(by_entity)):
            line = by_entity[l]
            line_sent = findSentiment(line)
            outfile.write(';;' + str(line_sent) + ';;' + line + '\n')
            by_sent = by_sent + line_sent
        outfile.close()
    return (about_sent, by_sent)

def printRemovedToFile(res_folder, entity, source, sentences):
    '''
    Write the removed sentences to a file
    :param entity: Entity Name
    :param source:  News source Short URL to be used in file naming
    :param sentences: set of removed sentences
    :return: None
    '''
    fname = './' + res_folder + '/removed_' + '_'.join(entity.split()) + '_' + source + '.txt'
    outfile = open(fname, 'w')
    for s in sentences:
        outfile.write(s + '\n')
    outfile.close()