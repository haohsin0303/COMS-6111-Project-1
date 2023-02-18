# COMS-6111-Project-1

This project is an implementation of an information retrieval system that aims to improve the search results returned by Google Search Engine API by exploiting user-provided relevance feedback. The goal of the project is to help users find more relevant search results and refine their queries.

## Teammembers
> Your name and Columbia UNI, and your teammate's name and Columbia UNI

- Christopher Asfour: cra2139
- Nina Hsu: hh2961

## Files
> A list of all the files that you are submitting

- AugmentQueryUtil.py
- FormatSearchResultUtil.py
- main.py
- README.md
- stopwords.txt

## How to run
> A clear description of how to run your program. Note that your project must run in a Google Cloud VM that you set up exactly following our instructions. Provide all commands necessary to install the required software and dependencies for your program.

1. Install the necessary Python packages using pip:
```
pip3 install google-client-api
pip3 install -U scikit-learn
```
2. Run the program using the following command:
```
python3 main.py <API Key> <Engine Key> <Precision> <Query>
```
    - API Key: The Google Custom Search Engine JSON API Key.
    - Engine Key: The Google Custom Search Engine ID.
    - Precision: The desired precision of the search results, it should be a decimal number between 0 and 1.
    - Query: The user's initial search query.

## General Description
> A clear description of the internal design of your project, explaining the general structure of your code (i.e., what its main high-level components are and what they do), as well as acknowledging and describing all external libraries that you use in your code

The project's internal design is composed of several modules that are responsible for different aspects of the query modification process. The main components of the project are:

1. `main.py`: This module is used to run the whole program. It takes the user query as input,
2. `FormatSearchResultUtil.py`: This module is responsible for formatting the search result from google search engine API.
3. `AugmentQueryUtil.py`: This module implements the TF-IDF and Rocchio algorithm; and orders the result with the highest scores. We use sklearn to help us with the TF-IDF vector calculation.

## Detailed Description
> A detailed description of your query-modification method (this is the core component of the project); this description should cover all important details of how you select the new keywords to add in each round, as well as of how you determine the query word order in each round

We first calculate the importance of words in these documents using the TF-IDF algorithm, which is implemented using the sklearn library. The TF-IDF algorithm assigns each word in the document a weight that reflects its importance.

We then use the Rocchio algorithm to identify the important terms to be added to the original query. The Rocchio algorithm takes the TF-IDF weights of the words in the relevant and non-relevant documents and generates a new query vector by combining the original query vector with the weighted sum of the relevant and non-relevant document vectors.

Once we have identified the new query terms, we apply finalizing processing steps to help narrow the search results.
First, if the new query terms have words that are the plural or singular versions of the initial query, we remove it since it does not provide additional context
to the desired query.
Second, if the weighted scores of the two new query terms have a large absolute difference, there is a probable chance that the term with the lowest weighted score could add additional complexity to the search results. Therefore, we remove it.
Third, we check if the combined new query terms are found in the summary of the search results. If so, we return. If not, we swap the new query terms
and perform the same check.

Once we finalize the new query terms, we may have to reorder the entire query itself to help narrow the search results. 
We do this by iterating over all possible permutations of the user query combined with the new query terms and calculating an ordering score for each permutation.
The ordering score is calculated by iterating over the summary search results and determining whether or not the summary
    a) has all the permutation terms in its text
    b) follows the same ordering as the terms in the permutation

The permutation that has the highest score will be returned and be used as the next query for the next iteration. 


## Google Custom Search Engine Credentials
> Your Google Custom Search Engine JSON API Key and Engine ID (so we can test your project)

- JSON API Key: AIzaSyBr5aenBL0VfH55raQJUMSYiOmdkspmzPY
- Search Engine ID: 089e480ae5f6ce283
