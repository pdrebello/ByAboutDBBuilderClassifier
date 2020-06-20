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
#import nltk
#nltk.download('punkt')
#from nltk.tokenize import sent_tokenize


    
class ExtractSentences:
    
    caps = "([A-Z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr|Rs)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Rs|Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"
    numbers = "1234567890"
    
    def find(self, s, ch):
        return [i for i, ltr in enumerate(s) if ltr == ch]
    
    def replacer(self, s, newstring, index, nofail=False):
        # raise an error if index is outside of the string
        if not nofail and index not in range(len(s)):
            raise ValueError("index outside given string")
    
        # if not erroring, but the index is still not in the correct range..
        if index < 0:  # add it to the beginning
            return newstring + s
        if index > len(s):  # add it to the end
            return s + newstring
    
        # insert the new string between "slices" of the original
        return s[:index] + newstring + s[index + 1:]
    def split_into_sentences(self,text):
        text = " " + text + "  "
        text = text.replace("\n"," ")
        text = re.sub(self.prefixes,"\\1<prd>",text)
        text = re.sub(self.websites,"<prd>\\1",text)
        if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
        text = re.sub("\s" + self.caps + "[.] "," \\1<prd> ",text)
        text = re.sub(self.acronyms+" "+self.starters,"\\1<stop> \\2",text)
        text = re.sub(self.caps + "[.]" + self.caps + "[.]" + self.caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
        text = re.sub(self.caps + "[.]" + self.caps + "[.]","\\1<prd>\\2<prd>",text)
        text = re.sub(" "+self.suffixes+"[.] "+self.starters," \\1<stop> \\2",text)
        text = re.sub(" "+self.suffixes+"[.]"," \\1<prd>",text)
        text = re.sub(" " + self.caps + "[.]"," \\1<prd>",text)
        if "\"" in text: text = text.replace(".\"","\".")
        if "!" in text: text = text.replace("!\"","\"!")
        if "?" in text: text = text.replace("?\"","\"?")
        full_stop_pos = self.find(text, ".")
        remove_pos = []
        dont_remove_pos = []
        for i in full_stop_pos:
            if(i == 0):
                remove_pos.append(i)
            elif(i == len(text)-1):
                remove_pos.append(i)
            elif((not(text[i-1] in self.numbers)) or (not(text[i+1] in self.numbers))):
                remove_pos.append(i)
            else:
                dont_remove_pos.append(i)
        for i,j in enumerate(remove_pos):
            text = self.replacer(text,".<stop>",j+i*6)
            
        #text = text.replace(".",".<stop>")
        text = text.replace("?","?<stop>")
        text = text.replace("!","!<stop>")
        
        text = text.replace("<prd>",".")
        sentences = text.split("<stop>")
        sentences = sentences[:-1]
        sentences = [s.strip() for s in sentences]
        return sentences
    
