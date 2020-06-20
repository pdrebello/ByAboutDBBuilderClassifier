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


def preprocesstext(doc_set):
    text = doc_set.lower()
    text = text.replace('\r', '')
    text = text.replace('\r\n', '')
    text = text.replace('\n', '')
    text = text.replace('"', '')
    text = text.replace('%', ' ')
    return text
def getabout(text1, sNLP):
    text=preprocesstext(text1)
    pos_text = sNLP.pos(text)
    parse_text = sNLP.dependency_parse(text)
    state1 = False
    state2 = False
    #print("Pos Text is"+str(pos_text))
    #print("Parse Text is"+str(parse_text))
    #for pt in parse_text:
        #print(pt)
        #print(pos_text[pt[1] - 1][0])
        #print(pos_text[pt[2] - 1][0])
    #print("!~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    for pt in parse_text:
        #print(pt)
        #print(pos_text[pt[1] - 1][0])
        #print(pos_text[pt[2] - 1][0])
        if ((pt[0] == 'nsubj') or (pt[0] == 'nmod') or (pt[0] == 'amod') or (pt[0] == 'dobj')): #and ((pos_text[pt[1] - 1][0] in entity_keywords) or (pos_text[pt[2] - 1][0] in entity_keywords)):
            if ((pt[0] == 'nsubj') and (
                            pos_text[pt[1] - 1][0] in fixed_keywords or pos_text[pt[2] - 1][0] in fixed_keywords)):
                state2 = True
                #action is the by keyword e.g "says", "said", "told" etc
                if(pos_text[pt[1] - 1][0] in fixed_keywords):
                    action = pos_text[pt[1] - 1][0]
                    doer=pos_text[pt[2]-1][0]
                else:
                    action = pos_text[pt[2] - 1][0]
                    doer=pos_text[pt[2]-1][0]
                #print("action inside after state2= True ")
                #print(action)
                #print("doer is " + str(doer))
            else:
                state1 = True
        #if a By statement   
    talking_about=[] 
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
        #print("complement  is  "+complement)
        if(ccomp):
            for pt in parse_text:
                if(pt[0] == 'nsubj'):
                    if((pos_text[pt[1] - 1][0] == complement)):
                        #Covers he will case
                        #print(" Talking about "+pos_text[pt[2] - 1][0])
                        if(pos_text[pt[2] - 1][1]=='NN' or pos_text[pt[2] - 1][1]=='NNS'):
                            talking_about.append(pos_text[pt[2] - 1][0])
                            #print(" "+str(pos_text[pt[2] - 1][0])+" has been added to talking about")
                            #find if there is a relative clause
                            for iter in parse_text:
                                if((iter[0]=='acl:relcl' or iter[0]=='acl') and iter[1]==pt[2]):
                                    if(pos_text[iter[2]-1][1]=='NN')or(pos_text[iter[2]-1][1]=='NNS') or(pos_text[iter[2]-1][1]=='JJ'):
                                        talking_about.append(pos_text[iter[2]-1][0])
                                    else:
                                        for niter in parse_text:
                                            if(niter[0]=='dobj' and niter[1]==iter[2]):
                                                #print(" **Talking about "+pos_text[niter[2]-1][0])
                                                talking_about.append(pos_text[niter[2]-1][0])
                                if(iter[0]=='nmod' and (iter[1]==pt[2] or iter[1]==pt[1])):
                                    talking_about.append(pos_text[iter[2]-1][0])

                        elif(pos_text[pt[2] - 1][1]=='PRP'):
                            toAppend=pos_text[pt[2] - 1][0]
                            #action_pos=parse_text[pt[1] - 1][1]
                            toAppend=toAppend+"(Possibly "+doer+" )"
                            talking_about.append(toAppend)
                            #print("Talking About: " + talking_about)
                    if((pos_text[pt[2] - 1][0] == complement)):
                        talking_about.append(pos_text[pt[1] - 1][0])
                        #print("Talking About: " + talking_about)
                elif(pt[0]=='dobj'):
                    if((pos_text[pt[1] - 1][0] == complement)):
                        talking_about.append(pos_text[pt[2] - 1][0])
                        for iter in parse_text:
                            if((iter[0]=='acl:relcl' or iter[0]=='acl') and iter[1]==pt[2]):
                                if(pos_text[iter[2]-1][1]=='NN')or(pos_text[iter[2]-1][1]=='NNS') or(pos_text[iter[2]-1][1]=='JJ'):
                                    talking_about.append(pos_text[iter[2]-1][0])
                                else:
                                    for niter in parse_text:
                                        if(niter[0]=='dobj' and niter[1]==iter[2]):
                                            #print(" **Talking about "+pos_text[niter[2]-1][0])
                                            talking_about.append(pos_text[niter[2]-1][0])
                            if(iter[0]=='nmod' and (iter[1]==pt[2] or iter[1]==pt[1])):
                                talking_about.append(pos_text[iter[2]-1][0])
                    if((pos_text[pt[2] - 1][0] == complement)):
                        talking_about.append( pos_text[pt[1] - 1][0])
                        for iter in parse_text:
                            if((iter[0]=='acl:relcl' or iter[0]=='acl') and iter[1]==pt[1]):
                                if(pos_text[iter[2]-1][1]=='NN')or(pos_text[iter[2]-1][1]=='NNS') or(pos_text[iter[2]-1][1]=='JJ'):
                                    talking_about.append(pos_text[iter[2]-1][0])
                                else:
                                    for niter in parse_text:
                                        if(niter[0]=='dobj' and niter[1]==iter[2]):
                                            #print(" **Talking about "+pos_text[niter[2]-1][0])
                                            talking_about.append(pos_text[niter[2]-1][0])
                            if(iter[0]=='nmod' and (iter[1]==pt[2] or iter[1]==pt[1])):
                                talking_about.append(pos_text[iter[2]-1][0])
                        #print("Talking About: " + talking_about)
                elif(pt[0]=='csubj'):
                    if((pos_text[pt[1] - 1][0] == complement)):
                        toFind=pt[2]
                        for iter in parse_text:
                            if(iter[1]==toFind):
                                talking_about.append(pos_text[iter[2]-1][0])

    #print("Abouts are "+str(talking_about))
    #print(text1 + "\n" + str(state1) + " " + str(state2) + " \n")
    return talking_about

if __name__ == "__main__":
    print("hi")
    sNLP = StanfordNLP()
    fixed_keywords = ['says', 'said', 'asks', 'asked', 'told', 'announced', 'announce', 'claimed', 'claim']
    while(True):
        print("Input the text:")
        text1=input()
        print(getabout(text1, sNLP))
    print("done")