from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
import itertools
from sklearn.metrics.pairwise import cosine_similarity

ALPHA = 1
BETA = 0.75
GAMMA = 0.15

COUNT = 1
Q0 = 0
R, NR, SUM_R, SUM_NR = 0, 0, 0, 0

orderingOfWords = []



def createTfIdf():
    """
    Creates a new instance of TfidfVectorizer
    """
    return TfidfVectorizer(analyzer="word", stop_words='english')

def transformUserQueryToVector(tf_idf, search_results, user_query):
    """
    Transforms the original user query into a vector using the search results
    and provided tf_idf object.
    Updates the Q0 vector 
    """
    global Q0
    tf_idf.fit_transform([result for result in search_results ])
    Q0 = tf_idf.transform(user_query)

def transformDocumentToVector(tf_idf, search_results, relevancy_doc ):
    """
    Transforms the list of documents into vectors  
    """
    
    global orderingOfWords
    tf_idf.fit_transform([result for result in search_results ])
    result = []

    for d in relevancy_doc:
        result.append(tf_idf.transform([d]))
        orderingOfWords.append(d)
    return result
    
def setRocchioParams(relevant_documents, irrelevant_documents):
   """
   Sets the values for the parameters used in the Rocchio algorithm for relevance feedback
   """
   global R, NR, SUM_R, SUM_NR
   R, NR = len(relevant_documents), len(irrelevant_documents)
   SUM_R, SUM_NR = sum(relevant_documents), sum(irrelevant_documents)


def runRocchio():
    """
    Runs the Rocchio algorithm with the global parameters
    Returns the new query vector
    """

    global ALPHA, BETA, GAMMA, R, NR, SUM_R, SUM_NR
    firstTerm = ALPHA * Q0
    secondTerm = BETA * (SUM_R / R)
    thirdTerm = GAMMA * (SUM_NR/ NR)

    return firstTerm + secondTerm - thirdTerm

def selectHighestValuedWords(tf_idf, q_vector, user_query):
    """
    Returns the list of the two highest-valued words by their TF-IDF score
    """

    # Stores the words present in the query vector through inverse transform
    inverse_transform = tf_idf.inverse_transform(q_vector)
    all_words = [word for words in inverse_transform for word in words]

    nonzero_indices = q_vector.nonzero()
    rows, columns = nonzero_indices[0], nonzero_indices[1]

    # Create a dictionary mapping each non-zero index to its corresponding value in q_vector
    tf_idf_dict = {}
    for i in range(len(rows)):
        pair = (rows[i], columns[i])
        tf_idf_dict[pair] = q_vector[pair]

    word_scores = dict(zip(all_words, list(tf_idf_dict.values())))
    highest_words = sorted(word_scores, key=lambda x: word_scores[x], reverse=True)

    # Filters out any words that are already in the original user query
    filtered = filter(lambda x: x not in user_query, highest_words)
    
    # Set the highest words to the filtered list along with removing any plural or singular versions of words found
    # in user_query
    highest_words = list(filtered)
    highest_words = removePluralOrSingular(highest_words, user_query)

    # Return immediately if we only have 1 word
    if (len(highest_words) < 2):
        return highest_words

    
    # Calculates the cosine similary between the user query and the 2 highest words
    highestWord1, highestWord2 = highest_words[:2]
    original_sim = cosine_similarity(q_vector, tf_idf.transform([user_query]))[0][0]
    firstWordSim = cosine_similarity(q_vector, tf_idf.transform(["{} {}".format(user_query, highestWord1)]))[0][0]
    secondWordSim = cosine_similarity(q_vector, tf_idf.transform(["{} {}".format(user_query, highestWord2)]))[0][0]

    # Checks if both the highest words are not similar to the original query and if so,
    # checks to see if any combination of the highest words is a substring of any of the sentence fragments
    if firstWordSim <= original_sim and secondWordSim <= original_sim:
        for sentenceFragment in orderingOfWords:
            if (" ".join(highest_words[:2]) in sentenceFragment):
                print("HERE: ", highest_words[:2])
                return highest_words[:2]
            else:
                swapped_highest_words_ordering = highest_words[:2][::-1] 
                if (" ".join(swapped_highest_words_ordering) in sentenceFragment):
                    print("HERE 2: ", swapped_highest_words_ordering)
                    return swapped_highest_words_ordering 

    # Otherwise, return either the first highest word or second highest word
    # depending on whose similarity score is higher. 
    if firstWordSim >= secondWordSim:
        print("HERE 3: ", highestWord1)
        return [highestWord1]
    else:
        print("HERE 4: ", highestWord2)
        return [highestWord2]



def maybeReorderWords(user_query, new_words):

    """
    Calculates all possible permutations of the combined query 
    and returns the best word ordering depending on their score
    calculated from the search results. 
    
    """

    # Combines user query with new words and generates all possible orderings
    combined_input = [user_query] + new_words
    possibleOrderings = list(itertools.permutations(combined_input))
    permutationScore = {}


    # Goes through all the possible orderings and stores their respective score
    for ordering in possibleOrderings:
        score = 0
        for sentenceFragment in orderingOfWords:
            score += calculateScore(ordering, sentenceFragment) 
        permutationScore[ordering] = score   

    # Return ordering with highest score
    bestPossibleOrdering = max(permutationScore, key=permutationScore.get)
    return bestPossibleOrdering

def calculateScore(ordering, sentenceFragment):
    """
    Given an ordering, calculates a score based on the position of words in the search result
    """

    words = sentenceFragment.split()
    last_visited_index = -1

    # Returns the score based on how close the ordering matches
    # the fragment's ordering
    for word in ordering:
        index = -1
        for i, w in enumerate(words):
            if (word.lower() == w.lower()):
                index = i
                break
        if index == -1 or index <= last_visited_index:
            return 0

        last_visited_index = index
    return 1

def removePluralOrSingular(words, target_word):
    """
    Removes the plural and singular versions of a word from a list of words.
    """
    new_words = words.copy()

    # Iterate over each word in the list
    for word in words:
        # Check if the word is a plural or singular version of the target word
        if word == target_word or word == makePlural(target_word):
            # If it is, remove it from the new list
            new_words.remove(word)

    # Return the modified list
    return new_words

def makePlural(word):
    """
    Returns the plural version of a given word.
    """
    # Add "es" to the end of the word if it ends in "s", "x", "z", "ch", or "sh"
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    # Change the "y" to "ies" if the word ends in a consonant followed by a "y"
    elif word[-1] == "y" and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    # Add "s" to the end of the word if it ends in a vowel followed by a "y"
    elif word[-1] == "y" and word[-2] in "aeiou":
        return word + "s"
    else:
        return word + "s"