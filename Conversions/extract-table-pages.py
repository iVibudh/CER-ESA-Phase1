# -*- coding: utf-8 -*-
"""
This file contains code to extract the pages of each document where a table
frame was identified. The results of this code serve as input to the primary
table extraction.
"""

import os
import json

import html_document

# extract table pages
"""
Please change the following variables to where you have the input and where
you want the output:
    INPUT_FOLDER:   the folder where all the HTML documents are stored
    OUTPUT_FOLDER:  the folder in which the data about the pages of documents 
                    with table frames will be dumped into. 2 text files will
                    be created in this folder:
                        "table-pages.txt":          a text file containing JSON encoded
                                                    data with the page numbers (starting from 0) 
                                                    of each document where a table frame
                                                    was identified.
                        "table-pages-failed.txt":   a text file containing the filenames
                                                    of all files from the INPUT_FOLDER that
                                                    failed to open or errored while running
                                                    this code
"""
INPUT_FOLDER = "W:/COE/coeprojects/NEB/2019_IN_Text_S52/05_Client_Deliverables/02 ESAs as structured html/"
OUTPUT_FOLDER = "W:/COE/coeprojects/NEB/2019_IN_Text_S52/03_WIP/Shawn/html/output/"


# container for results, maps filenames to a list of page indices where table frames
# were detected
result = {}
# list of filenames of all files that failed to open or errored while running
# the code
bad_files = []
for i, FILENAME in enumerate(os.listdir(INPUT_FOLDER)):
    print(i, FILENAME)
    try:
        with open(INPUT_FOLDER + FILENAME, 'r', encoding='utf-8') as f:
            # initialize document
            html_doc = html_document.html_document(f)
            # list of page indices where a table frame was detected
            pages = []
            for page_number, page in enumerate(html_doc.pages):
                # if the page has at least one table frame, add the page
                # index to the list
                has_table = False
                for image in page.images:
                    if image.is_table:
                        has_table = True
                        break
                if has_table:
                    pages.append(page_number)
            
            # add the pages with table frames of this document to the main
            # result
            result[''.join(FILENAME.split('.html')[:-1])] = pages
    except:
        bad_files.append(FILENAME)
        print('Errored on ' + FILENAME)

# write data in JSON format to a text file
with open(OUTPUT_FOLDER + "table-pages.txt", 'w+', encoding='utf-8') as output:
    output.write(json.dumps(result, indent=2))

# write filenames of files that failed to open or errored while running the code
# to a text file
with open(OUTPUT_FOLDER + "table-pages-failed.txt", 'w+', encoding='utf-8') as output:
    output.write('\n'.join(bad_files))
