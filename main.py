import string
import sys
import re
import pprint
from googleapiclient.discovery import build
from collections import Counter, defaultdict
import AugmentQueryUtil
import FormatSearchResultUtil
from googleapiclient.errors import HttpError

# search_engine_id = "089e480ae5f6ce283"
# json_api_key = "AIzaSyBr5aenBL0VfH55raQJUMSYiOmdkspmzPY"


API_KEY = None
ENGINE_KEY = None
PRECISION = 0
CALCULATED_PRECISION = -1
USER_QUERY = ""
stop_words = set()
termFrequency = {}
relevant_documents = defaultdict(int)
irrelevant_documents = defaultdict(int)
augmented_query_terms = []
NEW_QUERY_TERMS = []


# removing the new line characters
with open('stopwords.txt') as f:
    stop_words = {line.rstrip() for line in f}


def get_google_search_results():
    global USER_QUERY, NEW_QUERY_TERMS

    service = build("customsearch", "v1", developerKey=API_KEY)
    querying = True
    while querying:
        termFrequency, relevant_documents, irrelevant_documents = {}, defaultdict(int), defaultdict(int)
        if (len(NEW_QUERY_TERMS) > 0):
            USER_QUERY = USER_QUERY + " " + " ".join(NEW_QUERY_TERMS)
        write_parameters(PRECISION, USER_QUERY)
        try:
            res = (
            service.cse()
            .list(
                q=USER_QUERY,
                cx=ENGINE_KEY,
            )
            .execute()
            )
            querying = parse_search_results(res)
        except HttpError:
            print("API key or Engine key not valid. Please pass a valid API and Engine key.")
            querying = False

def write_feedback_summary():
    # ======================
    # FEEDBACK SUMMARY
    # Query milk
    # Precision 1.0
    # Desired precision reached, done
    # global calculated_precision

    print("\
====================== \n\
FEEDBACK SUMMARY \n\
Query {user_query} \n\
Precision {calculated_precision} \n\
Desired precision reached, done".format(user_query=USER_QUERY, calculated_precision=CALCULATED_PRECISION)
    )

def write_augment_query_summary():
    global USER_QUERY
    global NEW_QUERY_TERMS
    
    print("\
====================== \n\
FEEDBACK SUMMARY \n\
Query {user_query} \n\
Precision {calculated_precision} \n\
Still below the desired precision of {desired_precision} \n\
Indexing results .... \n\
Indexing results .... \n\
Augmenting by {new_query_terms}".format(user_query=USER_QUERY, calculated_precision=CALCULATED_PRECISION, desired_precision=PRECISION, new_query_terms=" ".join(NEW_QUERY_TERMS))
    )


def write_unable_to_augment_query_summary():
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
    print("\
====================== \n\
FEEDBACK SUMMARY \n\
Query {user_query} \n\
Precision {calculated_precision} \n\
Still below the desired precision of {desired_precision} \n\
Below desired precision, but can no longer augment the query".format(user_query=USER_QUERY, desired_precision=PRECISION, calculated_precision=CALCULATED_PRECISION)
)
    
def augment_query(google_search_results, relevant, not_relevant):
    tf_idf = AugmentQueryUtil.createTfIdf()

    AugmentQueryUtil.transformUserQueryToVector(tf_idf, google_search_results, [USER_QUERY])
    red = AugmentQueryUtil.transformDocumentToVector(tf_idf, google_search_results, relevant)
    nred = AugmentQueryUtil.transformDocumentToVector(tf_idf, google_search_results, not_relevant)

    AugmentQueryUtil.setRocchioParams(red, nred)

    q_vector = AugmentQueryUtil.runRocchio()

    # for word in termFrequency:
    #     splitted_user_query = user_query.split()
    #     if (word in splitted_user_query):
    #         q_vector[word] = 1
    #     else:
    #         q_vector[word] = 0
    
    # R = calculated_precision
    # NR = 10-calculated_precision
    # new_q = AugmentQueryUtil.run_rocchio(q_vector, relevant_documents, irrelevant_documents, termWeights, R, NR)

    new_words = AugmentQueryUtil.selectHighestValuedWords(tf_idf, q_vector, USER_QUERY)

    return new_words





def final_precision_zero_or_reached(total_search_results):
    global calculated_precision
    global augmented_query_terms
    global new_query_terms

    print("Calculated Precision: ", calculated_precision)
    print("Total Search Results", total_search_results)
    if ((calculated_precision / total_search_results) >= PRECISION):
        write_feedback_summary(total_search_results)
        return True
    elif (calculated_precision == 0):
        write_unable_to_augment_query_summary(total_search_results)
        return True
    else:
        new_query_terms = augment_query()
        augmented_query_terms += new_query_terms
        return False


    

def parse_search_results(res):
    global CALCULATED_PRECISION, NEW_QUERY_TERMS
    
    # total_search_results = len(res['items'])
    # old_query_length = len(augmented_query_terms)

    # calculated_precision = 0

    refined_search_results = []
    relevant, not_relevant = [], []

    for count, item in enumerate(res['items']):
        result_title = item['title']
        result_url = item['link']
        result_summary = item['snippet']

        # skip pdf files
        if len(result_url) >= 3 and result_url[-4:] == ".pdf":
            continue

        print("\
Result {iteration_count}\n\
[\n\
 URL: {result_url} \n\
 Title: {result_title} \n\
 Summary: {result_summary} \n\
] \n".format(iteration_count=count+1, result_url=result_url, result_title=result_title, result_summary=result_summary)
        )

        # parsed_words = calculate_term_frequency_for_document(result_summary)


        # result_body = FormatSearchResultUtil.getSearchResultBody(result_url)
        result_body = ''
        # print("RESULT BODY: ", result_body)
        combined_search_result_string = result_title + " " + result_summary + " " + result_body
        # print("COMBINED: " , combined_search_result_string)

        
        formatted_search_result = FormatSearchResultUtil.removeUnwantedChars(combined_search_result_string)
        refined_search_results.append(formatted_search_result)
        # print(formatted_search_result)

        relevancy = input("Relevant (Y/N)? ")
        if (relevancy.upper() == "Y"):
            relevant.append(formatted_search_result)



            # store_relevant_document(set(parsed_words))
        
        else:
            not_relevant.append(formatted_search_result)
            # store_irrelevant_document(set(parsed_words))
    
    numOfRelevantResults = len(relevant)
    numOfNonRelevantResults = len(not_relevant)

    CALCULATED_PRECISION = numOfRelevantResults / (numOfRelevantResults + numOfNonRelevantResults)
    if (CALCULATED_PRECISION == 0.0):
        write_unable_to_augment_query_summary()
        return False
    elif (CALCULATED_PRECISION >= PRECISION):
        write_feedback_summary()
        return False
    else:
        NEW_QUERY_TERMS = augment_query(refined_search_results, relevant, not_relevant)
        write_augment_query_summary()
        return True



    # result = final_precision_zero_or_reached(total_search_results)
    # if (len(augmented_query_terms) != old_query_length):
    #     write_augment_query_summary(total_search_results)
    #     return True
    # else:
    #     return not(result)


def store_irrelevant_document(words):
    global irrelevant_documents
    
    for word in words:
        if (word in irrelevant_documents.keys()):
            irrelevant_documents[word] += 1
        else:
            irrelevant_documents[word] = 1


def store_relevant_document(words):
    global relevant_documents

    for word in words:
        if (word in relevant_documents.keys()):
            relevant_documents[word] += 1
        else:
            relevant_documents[word] = 1

    

    # words = []
    # words = result_summary.split()
    # # print(words)

    # punctuations =  '''!()[]\{\};:'"\,<>./?@#$%^&*_~'''
    # words = [word.translate(str.maketrans('', '', punctuations)) for word in words if word.lower() not in stop_words]
    # if ('' in words):
    #     words.remove('')
    # wfreq = [words.count(w) for w in words]
    # relevant_document = (dict(zip(words,wfreq)))
    # relevant_documents = Counter(relevant_documents) + Counter(relevant_document)
    # print("Relevant Documents: ", relevant_documents)



def calculate_term_frequency_for_document(result_description):
    global termFrequency
    words = []
    words = result_description.split()
    # print(words)

    punctuations =  '''!()[]\{\};:'"\,<>./?@#$%^&*_~'''
    words = [word.translate(str.maketrans('', '', punctuations)) for word in words if word.lower() not in stop_words]
    if ('' in words):
        words.remove('')
    wfreq = [words.count(w) for w in words]
    newTermFrequency = (dict(zip(words,wfreq)))
    termFrequency = Counter(termFrequency) + Counter(newTermFrequency)

    return words




def write_parameters(precision, user_query):
    print("\
Parameters: \n\
Client key  = AIzaSyBr5aenBL0VfH55raQJUMSYiOmdkspmzPY \n\
Engine key  = 089e480ae5f6ce283 \n\
Query       = {user_query} \n\
Precision   = {precision} \n\
Google Search Results: \n\
======================".format(user_query=USER_QUERY, precision=PRECISION)

    )

def main():
    """
    
    
    """


    # Format Required: <google api key> <google engine id> <precision> <query>
    global USER_QUERY, PRECISION, API_KEY, ENGINE_KEY

    terminal_arguments = sys.argv[1:]
    # Return if the number of arguments provided is incorrect
    if (len(terminal_arguments) != 4):
        # Usage: /home/gkaraman/run <API Key> <Engine Key> <Precision> <Query>
        print("Format must be <API Key> <Engine Key> <Precision> <Query>")
        return

    
    API_KEY = terminal_arguments[0]
    ENGINE_KEY = terminal_arguments[1]

    precisionString = terminal_arguments[2]
    isPrecisionNumber = precisionString.replace('.','',1).isdigit()

    # Return if precision number not a valid number
    if (not(isPrecisionNumber)):
        print("Precision must be a valid number")
        return

    PRECISION = float(precisionString)

    # Return if precision number is too small or big
    if (PRECISION <= 0.0):
        print("Desired precision reached, done")
        return
    elif (PRECISION > 1.0):
        print("Precision should be a real number between 0 and 1")
        return
    # Start querying search results
    else:
        USER_QUERY = " ".join(terminal_arguments[3:])
        get_google_search_results()


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