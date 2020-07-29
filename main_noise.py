
# coding: utf-8

# In[6]:

from NDChild import NDChild
from time import clock
from random import choice
import csv
from datetime import datetime
import os
from sys import argv
from argparse import ArgumentParser
from Sentence import Sentence

#GLOBALS
rate = 0.02
conservativerate = 0.001
numberofsentences = 200000
threshold = .001

#language = "611" #English
#language = "584" #French
#language = "2253" #German
language = "3856" #Japanese

infoFile = open('orig4.txt','rU')

LD = []
NOISE = []

def pickASentence(languageDomain):
    
    return choice(languageDomain)

def createLD():
    for line in infoFile:
        [gramm01, inflStr, sentenceStr, grammStr, sentID, struID] = line.split("\t")
        sentenceStr = sentenceStr.rstrip()
        s = Sentence([grammStr, inflStr, sentenceStr]) #constructor creates sentenceList
        if grammStr == language:
            LD.append(s)
        else:
            NOISE.append(s)
        


####   MAIN
createLD()

aChild = NDChild(rate, conservativerate)

for i in range(numberofsentences):
    #with some probability choose from LD or NOISE
    if i%10 != 0:
        s = pickASentence(LD)
    else:
        s = pickASentence(NOISE)

    aChild.consumeSentence(s)
    

print aChild.grammar

        

infoFile.close()



# In[ ]:




# In[ ]:



