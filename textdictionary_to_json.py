# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 13:19:32 2019

@author: yazdsous
"""

#store the content of 1321 text files in a dictionary with file name as key
import os
import json
import pandas as pd

#path_txt = "C:/Users/yazdsous/Desktop/Data/Text/"

path_txt = "F:/Environmental Baseline Data/Version 2/Data/Text/"

textfiles = {}

# r=root, d=directories, f = files
for r, d, f in os.walk(path_txt):

    for file in f:
        if '.txt' in file:
            with open(os.path.join(r, file), encoding = 'utf8') as txtfile:
                textfiles[file] = txtfile.read().replace('\n', '')

#write the data object (textfiles) to the "json_file" file
with open('text_ESA.json', 'w') as json_file:
    json.dump(textfiles, json_file)
    
    
#json.load method reads the string from the file, parses the json data and populates a python dictionary with the data
with open('text_ESA.json') as json_file:
    data = json.load(json_file)
    


##############################TEST###############################    
os.getcwd()
df = pd.DataFrame.from_dict(data,orient='index', columns=['A'])
df1=df[0:10]
x = df1.A[8]
#################################################################
