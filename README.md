# COMS-6111-Project-1

This project is an implementation of an information retrieval system that aims to improve the search results returned by Google Search Engine API by exploiting user-provided relevance feedback. The goal of the project is to help users find more relevant search results and refine their queries.

## Team Members
- Christopher Asfour: cra2139
- Nina Hsu: hh2961

## Files
- AugmentQueryUtil.py
- FormatSearchResultUtil.py
- main.py
- README.md
- stopwords.txt
- proj1 transcript.pdf

## How to run
1. Install the necessary Python packages using pip:
```
pip3 install --upgrade google-api-python-client
pip3 install --upgrade setuptools wheel pip
pip3 install scikit-learn
pip3 install html2text
pip3 install requests_html
```
2. Run the program using the following command:
```
python3 main.py <API Key> <Engine Key> <Precision> <Query>
```
    - API Key: The Google Custom Search Engine JSON API Key.
    - Engine Key: The Google Custom Search Engine ID.
    - Precision: The desired precision of the search results. It should be a decimal number between 0 and 1.
    - Query: The user's initial search query.

## General Description

The project's internal design is composed of several modules that are responsible for different aspects of the query modification process. The main components of the project are:

1. `main.py`: This module is used to run the whole program. It performs all validation checks when user enters the program parameters, conducts the google search requests with the parameters, skip all the pdf files in the search result by filtering the file name, and handles all the output printed to the console.
2. `FormatSearchResultUtil.py`: This module is responsible for formatting the search result from google search engine API and executing a full search of the url body when the iteration count exceeds 5. We utilize the re library (regular expressions), 
html2text library to convert HTML text to string, and requests_html library to create an HTML session with the search result url. 
3. `AugmentQueryUtil.py`: This module implements the TF-IDF and Rocchio algorithm; and orders the result with the highest scores. We use sklearn to support with the TF-IDF vector calculation and cosine similarity to select the highest valued words.

## Detailed Description

We first calculate the importance of words in these documents using the TF-IDF algorithm, which is implemented using the sklearn library. The TF-IDF algorithm assigns each word in the document with a weight that reflects its importance.

We then use the Rocchio algorithm to identify the important terms to be added to the original query. The Rocchio algorithm takes the TF-IDF weights of the words in the relevant and non-relevant documents and generates a new query vector by combining the original query vector with the weighted sum of the relevant and non-relevant document vectors. We set the alpha, beta, and gamma parameters used for the Rocchio algorithm to 1.0, 0.75, and 0.15 respectively. These values were determined based on Stanford's NLP Rocchio algorithm recommendations [1].  

Once we have identified the new query terms, we apply finalizing processing steps to help narrow the search results.
First, if the new query terms have words that are the plural or singular versions of the initial query, we remove it since it does not provide any additional information to the desired query.
Second, if any of the highest word scores are deemed really low (i.e. < 0.0001), we stop augmenting the query and return the unable
to augment query summary.
Third, if the weighted scores of the two new query terms have a cosine similarity that is not similar to the resulting q vector, we check to see which ordering of the two new query terms is found in all of the short summaries. We check if the combined new query terms are found in the summary of the search results. If so, we return. If not, we swap the new query terms and perform the same check. 
Otherwise, we check to see which word has the highest similarity and return that word alone. If the two words are exactly equal, then we return both words.

Once we finalize the new query terms, we may have to reorder the entire query itself to help narrow the search results. 
We do this by iterating over all possible permutations of the user query combined with the new query terms and calculating an ordering score for each permutation based on its relative position. 
The ordering score is calculated by iterating over the summary search results and determining whether the summary
    a) has all the permutation terms in its text
    b) follows the same ordering as the terms in the permutation by calculating its relative position

The permutation that has the highest score will be returned and be used as the next query for the next iteration. 


## Google Custom Search Engine Credentials
- JSON API Key: AIzaSyBr5aenBL0VfH55raQJUMSYiOmdkspmzPY
- Search Engine ID: 089e480ae5f6ce283


## References
1. https://nlp.stanford.edu/IR-book/html/htmledition/the-rocchio71-algorithm-1.html
