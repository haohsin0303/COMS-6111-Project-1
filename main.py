import string
import sys
import re
import pprint
from googleapiclient.discovery import build
from collections import Counter

search_engine_id = "089e480ae5f6ce283"
json_api_key = "AIzaSyBr5aenBL0VfH55raQJUMSYiOmdkspmzPY"


precision = 0
calculated_precision = -1
user_query = ""
stop_words = []
relevant_documents = []
irrelevant_documents = []

termFrequency = {}


# removing the new line characters
with open('stopwords.txt') as f:
    stop_words = [line.rstrip() for line in f]


def get_google_search_results(user_query):
    service = build("customsearch", "v1", developerKey=json_api_key)

    res = (
        service.cse()
        .list(
            q=user_query,
            cx=search_engine_id,
        )
        .execute()
    )
    parse_search_results(res)
    return res
# 

def write_feedback_summary(total_search_results):
    # ======================
    # FEEDBACK SUMMARY
    # Query milk
    # Precision 1.0
    # Desired precision reached, done
    # global calculated_precision
    final_precision = calculated_precision / total_search_results

    print("\
====================== \n\
FEEDBACK SUMMARY \n\
Query {user_query} \n\
Precision {final_precision} \n\
Desired precision reached, done".format(user_query=user_query, final_precision=final_precision)
    )


def write_unable_to_augment_query_summary(total_search_results):
    """
    ======================
    FEEDBACK SUMMARY
    Query abc
    Precision 0.0
    Still below the desired precision of 0.7
    Indexing results ....
    Indexing results ....
    Augmenting by
    Below desired precision, but can no longer augment the query
    """

    final_precision = calculated_precision / total_search_results

    print("\
====================== \n\
FEEDBACK SUMMARY \n\
Query {user_query} \n\
Precision {final_precision} \n\
Still below the desired precision of {precision} \n\
Below desired precision, but can no longer augment the query".format(user_query=user_query, calculated_precision=calculated_precision, precision=precision, final_precision=final_precision)
    )
    


def calculate_final_precision(total_search_results):
    global calculated_precision
    print("Calculated Precision: ", calculated_precision)
    print("Total Search Results", total_search_results)
    if ((calculated_precision / total_search_results) >= precision):
        write_feedback_summary(total_search_results)
        return True
    elif (calculated_precision == 0):
        write_unable_to_augment_query_summary(total_search_results)
        return True
    else:
        #augment user query
        pass
    

def parse_search_results(res):
    global calculated_precision
    total_search_results = len(res['items'])

    while (not(calculate_final_precision(total_search_results))):
        calculated_precision = 0

        for cnt, i in enumerate(res['items']):
            result_title = i['title']
            result_url = i['link']
            result_summary = i['snippet']

            # skip pdf files
            if len(result_url) >= 3 and result_url[-4:] == ".pdf":
                continue

            print("\
Result {iteration_count}\n\
[\n\
    URL: {result_url} \n\
    Title: {result_title} \n\
    Summary: {result_summary} \n\
]".format(iteration_count=cnt+1, result_url=result_url, result_title=result_title, result_summary=result_summary)
            )

            relevancy = input("Relevant (Y/N)? ")
            if (relevancy.upper() == "Y"):
                # relevant_documents.append()

                calculate_term_frequency_for_document(result_summary)

                if (calculated_precision == -1):
                    calculated_precision = 0
                calculated_precision += 1
            
            else:
                # irrelevant_documents.append()
                pass



def calculate_term_frequency_for_document(result_description):
    global termFrequency
    words = []
    words = result_description.split()
    print(words)
    # hyphen_regex = 

    # re.sub("((?:\w+-)+\w+)", "", result_description)
    # print("result_description", result_description)

    punctuations =  '''!()[]\{\};:'"\,<>./?@#$%^&*_~'''
    words = [word.translate(str.maketrans('', '', punctuations)) for word in words if word.lower() not in stop_words]
    if ('' in words):
        words.remove('')
    wfreq = [words.count(w) for w in words]
    newTermFrequency = (dict(zip(words,wfreq)))
    termFrequency = Counter(termFrequency) + Counter(newTermFrequency)
    print(termFrequency)




def write_parameters(precision, user_query):
    print("\
Parameters: \n\
Client key  = AIzaSyBr5aenBL0VfH55raQJUMSYiOmdkspmzPY \n\
Engine key  = 089e480ae5f6ce283 \n\
Query       = {user_query} \n\
Precision   = {precision} \n\
Google Search Results:".format(user_query=user_query, precision=precision)
    )

def main():
    # <google api key> <google engine id> <precision> <query>

    terminal_arguments = sys.argv[3:]
    global precision
    precision = float(terminal_arguments[0])
    print("precision2", precision)
    if (precision < 0.0 or precision > 1.0):
        print("Precision should be a real number between 0 and 1")
        return
    elif (precision == 0.0):
        print("Desired precision reached, done")
        return
    user_query = terminal_arguments[1]
    write_parameters(precision, user_query)
    results = get_google_search_results(user_query)



if __name__ == "__main__":
    main()

"""""
Development Plan:
Input: User Query: List of Strings [“”, “”],  precision value: Float (0.0, 1.0)
Output: Top 10 results displayed as
Title:
URL:
Description:


Coding Steps:
Edge cases:
If( userQuery is empty OR precision is <= 0 ) return
Instantiate search engine id and JSON API KEY values
Input those values along with the input user query to https://github.com/googleapis/google-api-python-client/blob/main/samples/customsearch/main.py
Store queryResults 
iterationCount = 0
Edge case:
If (iterationCount == 0 AND len(queryResults) < 10): return
Iterate through exactly 10 of the sorted results in decreasing order given from Step 2
Declare a list of the most relevant words to add to the query []. 
Declare numOfYes = 0
For each result
Print out the formatted title, url, description:
Await user input if Relevant (Yes or No):
If the user says Yes:
Utilize jaccard’s coefficient or other scoring method to determine most frequently used rare terms not in the user query
Add that to the
numOfYes += 1
After user input is received, print out the next formatted title, url, description
Calculate precision value (numOfYes / len(queryResult) > 10 ? 10 : queryResult))
If user precision value has not been met, we append to the user query the two most relevant words from the list. 
Rerun step 2 until a precision value is met
Print done
"""