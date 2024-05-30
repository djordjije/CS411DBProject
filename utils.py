import re
from itertools import chain
import requests 

def is_image_url(url):
    try:
        response = requests.head(url)
        content_type = response.headers['Content-Type']
        if content_type.startswith('image/'):
            return True
        else:
            return False
    except Exception as e:
        print("Error occurred while checking the URL:", e)
        return False
    
def identify_potential_faculty_name_duplicates(faculty_name_list):
    '''
    1. Convert all names to Firstname Middlename Lastname
    2. Remove Middle Names
    '''

    # List of detected duplicates
    potential_duplicates = []

    # original, cleaned
    working_names = [[i,i] for i in faculty_name_list]

    # Filter for name representation issues
    for i, name_pair in enumerate(working_names):
        if "," in name_pair[0]: # Detect Lastname, Firstname
            name_split = name_pair[0].split(",")
            working_names[i][1] = name_split[1] + " " + name_split[0]
    
    # print ("Debug 1: ", working_names) #  Debug

    # Filter for case issues
    for i in range(len(working_names)):
        working_names[i][1] = working_names[i][1].lower()
    
    # print ("Debug 2: ", working_names) #  Debug

    # Filter for titles
    phd_titles = ["phd", "ph.d", "dr."]
    for phd_title in phd_titles:
        for i  in range(len(working_names)):
            working_names[i][1] = working_names[i][1].replace(phd_title, "")

    # Filter for periods, hyphenation issues
    strip_chars = [".", "-"]
    for strip_char in strip_chars:
        for i in range(len(working_names)):
            strip_chars = "."
            working_names[i][1] = working_names[i][1].replace(strip_char, "")        

    # Strip Whitespace
    for i in range(len(working_names)):
        working_names[i][1] =  working_names[i][1].strip()

    # print ("Debug 3: ", working_names) #  Debug

    # Filter for middle name issues
    for name_pair in working_names:
        name_split =  working_names[i][1].split(" ")
        if len(name_split) > 2:
            working_names[i][1] = name_split[0] + name_split[-1]

    # print ("Debug 4: ", working_names) #  Debug

    # Populate a dictionary to search for matches:
    pairs_dict = {}
    for pair in working_names:
        if pair[1] in pairs_dict.keys():
            pairs_dict[pair[1]].append(pair[0])
        else:
            pairs_dict[pair[1]] = [pair[0]]

    # Find potential duplicates
    potential_duplicates = [[first, pairs_dict[second][0]] for first, second in working_names if len(pairs_dict[second]) > 1]

    # Format potential_duplicates for pair uniqueness
    potential_duplicates = [i for i in potential_duplicates if (i[0]!=i[1])]

    # Flatten the list to return to the Dash app
    flat_potential_duplicates = list(chain.from_iterable(potential_duplicates))
    
    return flat_potential_duplicates