import AugmentQueryUtil
import FormatSearchResultUtil
import sys
from collections import defaultdict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from textwrap import dedent

# search_engine_id = "089e480ae5f6ce283"
# json_api_key = "AIzaSyBr5aenBL0VfH55raQJUMSYiOmdkspmzPY"

API_KEY = None
ENGINE_KEY = None
PRECISION = 0
CALCULATED_PRECISION = -1
USER_QUERY = ""
termFrequency = {}
relevant_documents = defaultdict(int)
irrelevant_documents = defaultdict(int)
augmented_query_terms = []
NEW_QUERY_TERMS = []
ITERATION_COUNT = 0


def get_google_search_results():
    """
    Initiates google querying process by taking the initial query
    and optionally appending the initial query to the new augmented query terms
    Returns if number of search results is less than 10 and throws exception if API or Engine key are invalid.
    """
    global USER_QUERY, NEW_QUERY_TERMS, ITERATION_COUNT

    service = build("customsearch", "v1", developerKey=API_KEY)
    querying = True
    while querying:
        ITERATION_COUNT += 1
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

            if (ITERATION_COUNT == 1 and len(res["items"]) < 10):
                print("Your query produced less than 10 results")
                querying = False
                return
            else:
                querying = parse_search_results(res)
        except HttpError:
            print("API key or Engine key not valid. Please pass a valid API and Engine key.")
            querying = False


def write_feedback_summary():
    """
    Prints to the console the summary when the program is finished and the
    desired precision has been reached
    """

    print(dedent("""
    ======================
    FEEDBACK SUMMARY
    Query {user_query}
    Precision {calculated_precision}
    Desired precision reached, done""".format(user_query=USER_QUERY, calculated_precision=CALCULATED_PRECISION)
    ))

def write_augment_query_summary(old_user_query):
    """
    Prints to the console the summary when the desired precision
    has not been reached but new words have been found to augment
    the user query
    """
    global USER_QUERY
    global NEW_QUERY_TERMS

    print(dedent("""
    ======================
    FEEDBACK SUMMARY
    Query {user_query}
    Precision {calculated_precision}
    Still below the desired precision of {desired_precision}
    Indexing results ....
    Indexing results ....
    Augmenting by {new_query_terms}""".format(user_query=old_user_query, calculated_precision=CALCULATED_PRECISION, desired_precision=PRECISION, new_query_terms=" ".join(NEW_QUERY_TERMS))
    ))


def write_unable_to_augment_query_summary():
    """
    Prints to the console the summary when the desired precision
    has not been reached and new words have not found to augment
    the user query
    """

    print(dedent("""
    ======================
    FEEDBACK SUMMARY
    Query {user_query}
    Precision {calculated_precision}
    Still below the desired precision of {desired_precision}
    Below desired precision, but can no longer augment the query""".format(user_query=USER_QUERY, desired_precision=PRECISION, calculated_precision=CALCULATED_PRECISION)
    ))


def augment_query(google_search_results, relevant, not_relevant):
    """
    The logic that finds the new words to augment the user query
    Utilizes AugmentQueryUtil.py to handle:
        1. Creating the TF_IDF vector
        2. Transforming the relevant and non-relevant documents to vectors
        3. Initializing the Rocchio algorithm parameters
        4. Running the Rocchio algorithm
        5. Returning the final 1 or 2 new words that augment the user query
    """
    tf_idf = AugmentQueryUtil.createTfIdf()

    AugmentQueryUtil.transformUserQueryToVector(tf_idf, google_search_results, [USER_QUERY])
    red = AugmentQueryUtil.transformDocumentToVector(tf_idf, google_search_results, relevant)
    nred = AugmentQueryUtil.transformDocumentToVector(tf_idf, google_search_results, not_relevant)

    AugmentQueryUtil.setRocchioParams(red, nred)

    q_vector = AugmentQueryUtil.runRocchio()

    new_words = AugmentQueryUtil.selectHighestValuedWords(tf_idf, q_vector, USER_QUERY)

    return new_words

def parse_search_results(res):
    """
    Handles the logic for iterating over the search results and asking for document relevancy
    from the user.
    We designate each search result as relevant or non-relevant bsaed on the user's input
    and calculate the current precision.
    We terminate the program and print the respective summary if the calculated precision is exactly
    0.0 or 1.0. 
    As long as the maximum number of iterations has not been reached, any precision in between [0.0, 1.0] 
    will trigger the augment_query() function 
    """
    global CALCULATED_PRECISION, NEW_QUERY_TERMS, USER_QUERY

    refined_search_results = []
    relevant, not_relevant = [], []

    for count, item in enumerate(res['items']):
        # Extracts title, url and summary
        result_title = item.get('title','none')
        result_url = item.get('link','none')
        result_summary = item.get('snippet', 'none')

        # skips pdf files
        if len(result_url) >= 3 and result_url[-4:] == ".pdf":
            continue

        # Print formatted result 
        print(dedent("""
        Result {iteration_count}
        [
         URL: {result_url}
         Title: {result_title}
         Summary: {result_summary}
        ]""".format(iteration_count=count+1, result_url=result_url, result_title=result_title, result_summary=result_summary)
        ))

        # result_body = FormatSearchResultUtil.getSearchResultBody(result_url)
        result_body = ""

        combined_search_result_string = result_title + " " + result_summary + " " + result_body
        
        formatted_search_result = FormatSearchResultUtil.removeUnwantedChars(combined_search_result_string)
        refined_search_results.append(formatted_search_result)

        relevancy = input("Relevant (Y/N)? ")
        if (relevancy.upper() == "Y"):
            relevant.append(formatted_search_result)
        else:
            not_relevant.append(formatted_search_result)
    
    numOfRelevantResults = len(relevant)
    numOfNonRelevantResults = len(not_relevant)
    CALCULATED_PRECISION = numOfRelevantResults / (numOfRelevantResults + numOfNonRelevantResults)

    # Terminates querying and writes unable to augment query summary when precision is 0
    if (CALCULATED_PRECISION == 0.0):
        write_unable_to_augment_query_summary()
        return False
    # Terminates querying and writes feedback summary when desired precision is reached 
    elif (CALCULATED_PRECISION >= PRECISION):
        write_feedback_summary()
        return False
    # Augment query when precision is not reached and restart querying process
    else:
        NEW_QUERY_TERMS = augment_query(refined_search_results, relevant, not_relevant)
        reordered_words = AugmentQueryUtil.maybeReorderWords(USER_QUERY, NEW_QUERY_TERMS)
        old_user_query = USER_QUERY
        USER_QUERY = " ".join(reordered_words)
        write_augment_query_summary(old_user_query)
        return True

def write_parameters(precision, user_query):
    """
    Prints to the console the valid parameters provided by the 
    user when the program is launched
    """
    print(dedent("""
    Parameters:
    Client key  = AIzaSyBr5aenBL0VfH55raQJUMSYiOmdkspmzPY
    Engine key  = 089e480ae5f6ce283
    Query       = {user_query}
    Precision   = {precision}
    Google Search Results:
    ======================""".format(user_query=USER_QUERY, precision=PRECISION)
    ))


def main():
    """
    Starting point of program that parses the terminal arguments
    and verifies that arguments are valid. 
    Once arguments are deemed valid, the querying function will be called
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