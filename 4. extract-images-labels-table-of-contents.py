# -*- coding: utf-8 -*-
"""
This file contains the code to extract images, table frames, and table of
contents from the html documents. The output is a folder for each document
with images/table frames, a text file with the table of contents lines and
captions, and a text file containing the labels for each image and table frame.
"""

import cv2 
import os
import json
import time

import html_analyzer
import html_document

# extract images, tables, and table of contents from html
"""
Please change the following variables to where you have the input and where
you want the output:
    INPUT_FOLDER:   the folder where all the HTML documents are stored
    OUTPUT_FOLDER:  the output folder where all the folders containing images,
                    captions, and table of contents should be dumped into. It
                    is strongly recommended that the output folder be empty 
                    before running this code, as it will produce over 2000 folders.
                    In addition to the document folders, the OUTPUT_FOLDER will
                    contain a single text file:
                        "bad-files.txt":    a text file containing the filenames of all HTML documents
                                            in INPUT_FOLDER that failed to open, or errored somewhere
                                            while running the code
                    Every folder in OUTPUT_FOLDER will have the following files:
                        image or table frame .png files:    every image and table frame extracted from
                                                            the document as .png files. Example filenames
                                                            are "image_page-53_image-0.png" and
                                                            "table_page-0_image-0.png"
                        "label_log.txt":                    a text file containing data for the .png images
                                                            in JSON format. Information includes the filename,
                                                            the type of image ("image" or "table"), the
                                                            page number it was extracted from (page numbers in
                                                            this output start from 0), the vertical index in
                                                            the page it was extracted from (so if two images
                                                            were extracted from the page, the top one would
                                                            get an index of 0, and the other one would get an
                                                            index of 1), and the labels it was tagged with
                                                            (from both the page and from the table of contents).
                        "table-of-contents.txt":            a text file containing the labels extracted from
                                                            the document's table of contents, as well as the
                                                            text lines extracted from the table of contents.
                                                            Data is stored in JSON format.
"""
INPUT_FOLDER = "F:/D&IMBU/DataScience/2019.10.07 - Environmental Baseline Team Project/Demo Deliverables/Converted HTML Files"
OUTPUT_FOLDER = "F:/D&IMBU/DataScience/2019.10.07 - Environmental Baseline Team Project/Demo Deliverables/Codes"


INPUT_FOLDER = "F:/Environmental Baseline Data/Version 2/Data/HTML/"
OUTPUT_FOLDER = "C:/Users/singvibu/Desktop/5. outrput/"

# initialize some variables for profiling how long the code takes
start_time = time.time()
documents_processed = 0

# list of filenames which were unable to open or errored somewhere in this
# code
bad_files = []

for file_no, FILENAME in enumerate(os.listdir(INPUT_FOLDER)):
    print(file_no,FILENAME)




for file_no, FILENAME in enumerate(os.listdir(INPUT_FOLDER)):
    # if the filename does not end with .html, skip the file
    if len(FILENAME.split('.')) < 2 or FILENAME.split('.')[-1] != 'html': continue
    try:
        with open(INPUT_FOLDER + FILENAME, 'r', encoding='utf-8') as f:
            print(file_no, FILENAME)
            """
                Setup document
            """
            html_doc = html_document.html_document(f, extract_images=True)
            
            """
                Setup folder for the document images, tables, and captions
                to be dumped into
            """
            FILENAME = ''.join(FILENAME.split('.html')[:-1]).strip()
            if not os.path.exists(OUTPUT_FOLDER + FILENAME):
                os.makedirs(OUTPUT_FOLDER + FILENAME)
            
            # create containers for the output data to be stored in
            output_toc = {}
            output_labels = []
            
            """
                Get table of contents and the captions within it
            """
            toc_labels = {}
            toc_text = []
            toc_pages, toc_page_numbers = html_analyzer.get_toc_pages(html_doc)
            for toc_page in toc_pages:
                # add the extracted labels and text from this table of contents page
                # to the existing result
                toc_labels = {**toc_labels, **html_analyzer.extract_toc_labels(toc_page)}
                toc_text += list(map(lambda text_line: text_line + '\n', toc_page.text_lines))
            
            """
                Write what was extracted from the table of contents into file
            """
            with open(OUTPUT_FOLDER + FILENAME + "/table-of-contents.txt", "w+", encoding="utf-8") as toc_file:
                output_toc['toc_labels'] = toc_labels
                output_toc['raw_text'] = toc_text
                toc_file.write(json.dumps(output_toc, indent=2))
            
            
            """
                Attempt to tag images
            """
            # store the result of tagging images from the previous page, these
            # results are needed to detect tables that span multiple pages
            previous_page_tagged_images = None
            for page_number, page in enumerate(html_doc.pages):         
                labels = html_analyzer.extract_labels(page)
                
                # only use the table of contents captions if the page is after the
                # table of contents
                if len(toc_pages) == 0 or page_number < toc_page_numbers[0]:
                    tagged_images = html_analyzer.tag_images(page, page.images, labels, {}, previous_page_tagged_images=previous_page_tagged_images)
                else:
                    tagged_images = html_analyzer.tag_images(page, page.images, labels, toc_labels, previous_page_tagged_images=previous_page_tagged_images)
                
                previous_page_tagged_images = tagged_images
                
                for image_number, image_tagged in enumerate(tagged_images):
                    if image_tagged.image_data.is_table:
                        img_type = 'table'
                    else:
                        img_type = 'image'
                    
                    """
                        Save image to a .png file and record the label associated with it
                    """
                    cv2.imwrite(OUTPUT_FOLDER + FILENAME + "/{}_page-{}_{}-{}.png".format(img_type, page_number, img_type, image_number), image_tagged.image_data.image)
                    output_labels.append({
                            'file': "{}_page-{}_{}-{}.png".format(img_type, page_number, img_type, image_number),
                            'type': img_type,
                            'page-number': page_number,
                            'image-number': image_number,
                            'page-label': image_tagged.label.text if image_tagged.label else None,
                            'toc-label': image_tagged.toc_label
                        })
            
            """
                Write labels to file
            """
            with open(OUTPUT_FOLDER + FILENAME + "/label_log.txt", "w+", encoding="utf-8") as image_log_file:
                image_log_file.write(json.dumps(output_labels, indent=2))
                
    
        documents_processed += 1
    except:
        bad_files.append(FILENAME)

# print files that failed to open or errored when running the code
print(bad_files)
# save these bad files in a text log in the output folder
with open(OUTPUT_FOLDER + '/bad-files.txt', 'w+', encoding='utf-8') as bad_files_file:
    bad_files_file.write('\n'.join(bad_files))

# print the time taken for the analysis and the average time per document
time_taken = time.time() - start_time
print(float(time_taken) / documents_processed)
