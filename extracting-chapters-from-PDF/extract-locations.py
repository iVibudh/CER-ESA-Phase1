# -*- coding: utf-8 -*-
"""
This file contains code to extract locations from the html documents. It also
contains code to clean these locations (filter outliers) as well as produce
some additional files from the results, such as shapefiles.
"""

import os
import json
import pandas as pd

import html_analyzer
import html_document
import gis_converter


# location extraction with regular expressions
"""
Please change the following variables to where you have the input and where
you want the output:
    INPUT_FOLDER:   the folder where all the HTML documents are stored
    OUTPUT_FOLDER:  the output folder where the results of the location
                    extraction will be stored. The following files will be created:
                        "locations-raw.txt":        a text file containing the raw locations (before removing outliers)
                                                    from all documents. Data is stored in JSON format.
                                                    The page numbers for locations start from 0.
                        "bad-files.txt":            a text file containing the filenames of all files from INPUT_FOLDER
                                                    that failed to open or errored while running this script.
                        "summary-raw.txt":          a text file containing a summary log of how many documents were detected
                                                    to use a certain location format.
                        "locations-cleaned.txt":    a text file containing the same information as "locations-raw.txt", but
                                                    with outliers removed.
                                                    The page numbers for locations start from 0.
                        "summary.txt"               a text file containing a summary log of how many documents were detected
                                                    to use a certain location format, using the cleaned location data.
                        "location_counts.csv":      a csv file containing a table for storing information on how many locations
                                                    were detected per document. Duplicate locations in a document are counted, and
                                                    Mainline Valve locations are not included in the count.
                        "lat_long_points.dbf",
                        "lat_long_points.shx",
                        "lat_long_points.shp":      shapefile data containing points representing all locations that can be
                                                    converted to latitude-longitude (lat-longs, DLS, and NTS locations)
    INTERACTIVE_VISUALIZATION_FOLDER:   the folder in which the HTML, CSS, and JavaScript files for the interactive map
                                        visualization is stored. This code will output the location data in a JavaScript
                                        file into this folder so it can be loaded by the visualization. The file created
                                        will be named "locations.js", and will contain a JSON object representing the data
                                        from "locations-cleaned.txt".
"""
INPUT_FOLDER = "W:/COE/coeprojects/NEB/2019_IN_Text_S52/05_Client_Deliverables/02 ESAs as structured html/"
OUTPUT_FOLDER = "W:/COE/coeprojects/NEB/2019_IN_Text_S52/03_WIP/Shawn/html/output-locations/"
INTERACTIVE_VISUALIZATION_FOLDER = "W:/COE/coeprojects/NEB/2019_IN_Text_S52/03_WIP/Shawn/html/output-locations/interactive-map/"


# initialize variables to count number of documents with a certain location
# format
num_lat_long = 0
num_dls = 0
num_nts = 0
num_mlv = 0

num_files = 0
num_files_tagged = 0

# container for results to be converted to JSON later
result = {}
# list of files that failed to open or errored when running the code
bad_files = []

for file_no, FILENAME in enumerate(os.listdir(INPUT_FOLDER)):
    try:
        with open(INPUT_FOLDER + FILENAME, 'r', encoding='utf-8') as f:
            print(file_no, FILENAME)
            
            # dictionaries containing data about the locations identified
            # in the document
            lat_long_tags = {}
            dls_tags = {}
            nts_tags = {}
            mlv_tags = {}
            
            def _add_to_hist(locations_container, locations, page):
                """
                    Adds all locations in a list of locations to a dictionary 
                    in a histogram-like fashion (if the location already exists, 
                    just increment the count and add the page number, don't 
                    introduce another location in the dictionary.)
                """
                for location in locations:
                    if location.text in locations_container:
                        locations_container[location.text]['count'] += 1
                        locations_container[location.text]['pages'].append(page)
                    else:
                        locations_container[location.text] = {
                            'count': 1,
                            'pages': [page],
                            'tuple': location
                        }
                        try:
                            locations_container[location.text]['latitude-longitude'] = location.lat_long
                        except AttributeError:
                            pass
            
            
            # initialize document
            html_doc = html_document.html_document(f, extract_images=False)
            for page_number, page in enumerate(html_doc.pages):
                # find locations on the page and add to the dictionary for the
                # location format
                lat_long, dls, nts, mlv = html_analyzer.find_location_tags(page)
                    
                _add_to_hist(lat_long_tags, lat_long, page_number)
                _add_to_hist(dls_tags, dls, page_number)
                _add_to_hist(nts_tags, nts, page_number)
                _add_to_hist(mlv_tags, mlv, page_number)
                
            
            """
                Refactor the histogram-like dictionaries to lists so they can
                be converted effectively to json
            """
            lat_long_tags = [
                    {
                        'text': tag_text,
                        'count': tag['count'],
                        'pages': tag['pages'],
                        
                        # format-specific fields
                        'degrees-north': tag['tuple'].N,
                        'degrees-west': tag['tuple'].W
                    }
                for tag_text, tag in lat_long_tags.items()]
            
            dls_tags = [
                    {
                        'text': tag_text,
                        'count': tag['count'],
                        'pages': tag['pages'],
                        
                        # format-specific fields
                        'legal_subdivision': tag['tuple'].legal_subdivision,
                        'section': tag['tuple'].section,
                        'township': tag['tuple'].township,
                        'range': tag['tuple'].range,
                        'meridian': tag['tuple'].meridian,
                        
                        'latitude-longitude': {
                            'text': tag['latitude-longitude'].text,
                            'degrees-north': tag['latitude-longitude'].N,
                            'degrees-west': tag['latitude-longitude'].W
                        }
                    }
                for tag_text, tag in dls_tags.items()]
            
            nts_tags = [
                    {
                        'text': tag_text,
                        'count': tag['count'],
                        'pages': tag['pages'],
                        
                        # format-specific fields
                        'quarter_unit': tag['tuple'].quarter_unit,
                        'unit': tag['tuple'].unit,
                        'block': tag['tuple'].block,
                        'series_number': tag['tuple'].series_number,
                        'map_area': tag['tuple'].map_area,
                        'map_sheet': tag['tuple'].map_sheet,
                        
                        'latitude-longitude': {
                            'text': tag['latitude-longitude'].text,
                            'degrees-north': tag['latitude-longitude'].N,
                            'degrees-west': tag['latitude-longitude'].W
                        }
                    }
                for tag_text, tag in nts_tags.items()]
            
            mlv_tags = [
                    {
                        'text': tag_text,
                        'count': tag['count'],
                        'pages': tag['pages'],
                        
                        # format-specific fields
                        'valve': tag['tuple'].valve,
                        'offset': tag['tuple'].offset
                    }
                for tag_text, tag in mlv_tags.items()]
            
            # store the result of location extraction on this document in the
            # main result dictionary
            result[''.join(FILENAME.split('.html')[:-1])] = {
                    'latitude-longitude': lat_long_tags,
                    'dominion-land-survey': dls_tags,
                    'national-topographic-system': nts_tags,
                    'mainline-valve': mlv_tags
                    }
            
            # add to the counter for the of documents with a certain location format
            num_lat_long += len(lat_long_tags) > 0
            num_dls += len(dls_tags) > 0
            num_nts += len(nts_tags) > 0
            num_mlv += len(mlv_tags) > 0
            
            if len(lat_long_tags) > 0 or len(dls_tags) > 0 or len(nts_tags) > 0 or len(mlv_tags) > 0:
                num_files_tagged += 1
            
            num_files += 1
    except:
        bad_files.append(FILENAME)
        print('Error in ' + FILENAME)

# store the raw locations extracted in a text file in JSON format
with open(OUTPUT_FOLDER + 'locations-raw.txt', 'w+', encoding='utf-8') as output:
    output.write(json.dumps(result, indent=2))

# save names of files that failed to open or errored when running this code
# into a text log in the output folder
with open(OUTPUT_FOLDER + 'bad-files.txt', 'w+', encoding='utf-8') as output:
    output.write('\n'.join(bad_files))

# save the summary of how many files were identified with each location
# format into a summary text file
with open(OUTPUT_FOLDER + 'summary-raw.txt', 'w+', encoding='utf-8') as output:
    output.write('{} out of {} files were tagged ({}%)\n'.format(num_files_tagged, num_files, 100 * float(num_files_tagged) / num_files))
    output.write('{} out of {} files contained latitude-longitude coordinates ({}%)\n'.format(num_lat_long, num_files, 100 * float(num_lat_long) / num_files))
    output.write('{} out of {} files contained Dominion Land Survey coordinates ({}%)\n'.format(num_dls, num_files, 100 * float(num_dls) / num_files))
    output.write('{} out of {} files contained National Topographic System coordinates ({}%)\n'.format(num_nts, num_files, 100 * float(num_nts) / num_files))
    output.write('{} out of {} files contained Mainline Valve locations ({}%)\n'.format(num_mlv, num_files, 100 * float(num_mlv) / num_files))

#%% some cleaning of the locations (remove outliers)
# set the working folder to the output folder of the previous chunk of code
WORK_FOLDER = OUTPUT_FOLDER

"""
    Load raw location data
"""
with open(WORK_FOLDER + 'locations-raw.txt', 'r', encoding='utf-8') as inp:
    location_data = json.load(inp)
    
    
def check_dls(dls):
    """
    Function to check if a DLS location is reasonable
    """
    lat_long = dls['latitude-longitude']
    # check latitude is reasonable (within the region DLS covers)
    if not (lat_long['degrees-north'] >= 49 and lat_long['degrees-north'] <= 60):
        # dls location is not in BC, Alberta, Sask. or Manitoba
        return False
    # check longitude is reasonable (doesn't go too far into the next meridian)
    if dls['meridian'] == 'P':
        next_meridian = 2
    else:
        next_meridian = dls['meridian'] + 1
    
    if not ((lat_long['degrees-west'] >= gis_converter.dls_meridian_to_longitude(dls['meridian']) - 2) and
        (lat_long['degrees-west'] <= gis_converter.dls_meridian_to_longitude(next_meridian) + 2)):
        # dls location not within reasonable range for its meridian
        return False
    
    return True


def check_lat_long(lat_long):
    """
    Function to check if a lat-long location is reasonable
    """
    # check that the latitude-longitude coordinate is within Canada
    return (lat_long['degrees-west'] >= 50.5 and lat_long['degrees-west'] <= 160 and 
            lat_long['degrees-north'] >= 40 and lat_long['degrees-north'] <= 67)


for file, locations in location_data.items():
    # filter dls outliers
    locations['dominion-land-survey'] = list(filter(check_dls, locations['dominion-land-survey']))
    
    # convert lat-longs in the Eastern hemisphere to the Western hemisphere
    for lat_long in locations['latitude-longitude']:
        if lat_long['degrees-west'] < 0:
            lat_long['degrees-west'] = -1 * lat_long['degrees-west']
    # filter lat-long outliers
    locations['latitude-longitude'] = list(filter(check_lat_long, locations['latitude-longitude']))
            

# save the cleaned location data into a text file
with open(WORK_FOLDER + 'locations-cleaned.txt', 'w+', encoding='utf-8') as output:
    output.write(json.dumps(location_data, indent=2))


#%% generate a new summary file after filtering out outliers
# load the cleaned location data
with open(WORK_FOLDER + 'locations-cleaned.txt', 'r', encoding='utf-8') as cleaned_file:
    cleaned_locations = json.load(cleaned_file)

# initialize variables to count number of documents with a certain location
# format
num_files = len(cleaned_locations)
num_tagged = 0
num_dls = 0
num_nts = 0
num_mlv = 0
num_lat_long = 0

# count the number of files with a certain location format
for filename in cleaned_locations:
    file = cleaned_locations[filename]
    dls_tagged = len(file['dominion-land-survey']) > 0
    nts_tagged = len(file['national-topographic-system']) > 0
    mlv_tagged = len(file['mainline-valve']) > 0
    lat_long_tagged = len(file['latitude-longitude']) > 0
    
    if dls_tagged or nts_tagged or mlv_tagged or lat_long_tagged: num_tagged += 1
    
    num_dls += dls_tagged
    num_nts += nts_tagged
    num_mlv += mlv_tagged
    num_lat_long += lat_long_tagged

# output results of summary into a text file
with open(OUTPUT_FOLDER + 'summary.txt', 'w+', encoding='utf-8') as output:
    output.write('{} out of {} files were tagged ({}%)\n'.format(num_tagged, num_files, 100 * float(num_tagged) / num_files))
    output.write('{} out of {} files contained latitude-longitude coordinates ({}%)\n'.format(num_lat_long, num_files, 100 * float(num_lat_long) / num_files))
    output.write('{} out of {} files contained Dominion Land Survey coordinates ({}%)\n'.format(num_dls, num_files, 100 * float(num_dls) / num_files))
    output.write('{} out of {} files contained National Topographic System coordinates ({}%)\n'.format(num_nts, num_files, 100 * float(num_nts) / num_files))
    output.write('{} out of {} files contained Mainline Valve locations ({}%)\n'.format(num_mlv, num_files, 100 * float(num_mlv) / num_files))

#%% generate the JavaScript file with a JSON object so it can be loaded into the visualization
# load cleaned location data
with open(WORK_FOLDER + 'locations-cleaned.txt', 'r', encoding='utf-8') as cleaned_file:
    cleaned_locations_text = cleaned_file.read()

# save JavaScript file
with open(INTERACTIVE_VISUALIZATION_FOLDER + 'locations.js', 'w+', encoding='utf-8') as output_js:
    output_js.write('const locations = ' + cleaned_locations_text)

    
#%% generate a .csv file with number of locations per document (excluding Mainline Valve locations)
# load cleaned location data
with open(WORK_FOLDER + 'locations-cleaned.txt', 'r', encoding='utf-8') as cleaned_file:
    cleaned_locations = json.load(cleaned_file)
    
def get_count(locations):
    """
    Returns the total number of locations of a certain location format.
    This function counts duplicate locations, so a location mentioned
    twice in a document would be counted twice.
    """
    count = 0
    for location in locations:
        count += location['count']
    return count

# columns of the dataframe of filenames with their respective
# number of locations
files = []
num_locations_list = []

# counters for the total number of locations in all documents
# and the total number of unique locations in all documents
# excludes Mainline Valve locations from this count
total_locations = 0
unique_locations = 0
    
for file, locations in cleaned_locations.items():
    num_locations = get_count(locations['latitude-longitude']) + get_count(locations['dominion-land-survey']) + get_count(locations['national-topographic-system']) #+ get_count(locations['mainline-valve'])
    
    total_locations += num_locations
    unique_locations += len(locations['latitude-longitude']) + len(locations['dominion-land-survey']) + len(locations['national-topographic-system']) #+ len(locations['mainline-valve'])
    
    
    files.append(file)
    num_locations_list.append(num_locations)
    
# save the location counts into a .csv file, ordered from most to least number of locations.
# in this .csv file, duplicate locations in documents are counted.
csv_df = pd.DataFrame({'filename': files, 'number_of_locations': num_locations_list})
csv_df = csv_df.sort_values(by=['number_of_locations'], ascending=False)
csv_df = csv_df.reset_index(drop=True)

csv_df.to_csv(WORK_FOLDER + 'location_counts.csv')

#%% create shapefile with all lat-long, dls, and nts locations as latitude-longitude
#   coordinates for plotting

# load cleaned location data
with open(WORK_FOLDER + 'locations-cleaned.txt', 'r', encoding='utf-8') as cleaned_file:
    cleaned_locations = json.load(cleaned_file)

# a list of all latitude-longitude coordinates corresponding to locations
all_lat_longs = []

# add all locations that have a latitude-longitude representation (DLS, NTS, and
# latitude-longitude coordinates) to the list
for filename in cleaned_locations:
    file = cleaned_locations[filename]
    for lat_long in file['latitude-longitude']:
        all_lat_longs.append(lat_long)
    for dls_or_nts in file['dominion-land-survey'] + file['national-topographic-system']:
        all_lat_longs.append(dls_or_nts['latitude-longitude'])

# write the latitude-longitude coordinates into a shapefile so the locations
# can be easily plotted using GIS software
import shapefile
points = shapefile.Writer(WORK_FOLDER + 'lat_long_points')
points.field('name', 'C')
for lat_long in all_lat_longs:
    points.point(-1 * lat_long['degrees-west'], lat_long['degrees-north'])
    points.record(lat_long['text'])
points.close()
