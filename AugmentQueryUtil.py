import math
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import itertools
import inflect

ALPHA = 1
BETA = 0.75
GAMMA = 0.15

COUNT = 1
Q0 = 0
R, NR, SUM_R, SUM_NR = 0, 0, 0, 0

orderingOfWords = []

inflect = inflect.engine()


def createTfIdf():
    return TfidfVectorizer(analyzer="word", stop_words='english')

def transformUserQueryToVector(tf_idf, search_results, user_query):
    global Q0
    tf_idf.fit_transform([result for result in search_results ])
    Q0 = tf_idf.transform(user_query)

def transformDocumentToVector(tf_idf, search_results, relevancy_doc ):
    global COUNT, orderingOfWords
    tf_idf.fit_transform([result for result in search_results ])
    result = []
    ## {word: [(id of Document, index position)], word2: ...}
    ## 
    ##


    for d in relevancy_doc:
        result.append(tf_idf.transform([d]))
        # for index, word in enumerate(splitted_words):
        #     if (word in orderingOfWords.keys()):
        #         orderingOfWords[word].append((COUNT, index))
        #     else:
        #         orderingOfWords[word] = [(COUNT, index)]
        orderingOfWords.append(d)
        COUNT += 1
    return result
    
def setRocchioParams(relevant_documents, irrelevant_documents):
    global R, NR, SUM_R, SUM_NR
    R, NR = len(relevant_documents), len(irrelevant_documents)
    SUM_R, SUM_NR = sum(relevant_documents), sum(irrelevant_documents)


def runRocchio():
    global ALPHA, BETA, GAMMA, R, NR, SUM_R, SUM_NR
    firstTerm = ALPHA * Q0
    secondTerm = BETA * (SUM_R / R)
    thirdTerm = GAMMA * (SUM_NR/ NR)

    return firstTerm + secondTerm - thirdTerm

def selectHighestValuedWords(tf_idf, q_vector, user_query):
    inverse = tf_idf.inverse_transform(q_vector)

    all_words = []
    for words in inverse:
        for word in words:
            all_words.append(word)


    rows, columns = q_vector.nonzero()
    indices = []
    tf_idf_dict = {}
    for i in range(len(rows)):
        indices.append((rows[i], columns[i]))
    for index in indices:
        tf_idf_dict[index] = q_vector[index]

    
    word_scores = dict(zip(all_words, list(tf_idf_dict.values())))
    highest_words = sorted(word_scores, key=lambda x: word_scores[x], reverse=True)

    filtered = filter(lambda x: x not in user_query, highest_words)
    
    highest_words = list(filtered)
    if (len(highest_words) < 2):
        return highest_words

    print("DIFFERENCE: ", abs(word_scores[highest_words[0]] - word_scores[highest_words[1]]))

    highest_words = remove_plural_and_singular(highest_words, user_query)
    
    if (abs(word_scores[highest_words[0]] - word_scores[highest_words[1]]) > .1):
        return highest_words[:1]

    for sentenceFragment in orderingOfWords:
        if (" ".join(highest_words[:2]) in sentenceFragment):
            return highest_words[:2]
        else:
            swapped_highest_words_ordering = highest_words[:2][::-1] 
            print(swapped_highest_words_ordering)
            if (" ".join(swapped_highest_words_ordering) in sentenceFragment):
                return swapped_highest_words_ordering 

    


    return highest_words[:2]


def maybeReorderWords(user_query, new_words):
    
    # User Query: brin
    # New Word: sergey microsoft

    combined_input = [user_query] + new_words

    possibleOrderings = list(itertools.permutations(combined_input))

    permutationScore = {}

    ## In each n-gram tuple, does the tuple follow the ordering defined? 
    ## After the iteration is done, store final count and we do the next possible ordering of words and restart

    ## After all permutations are complete: check which ordering has the highest score and let that be the final augmented query
 

    for ordering in possibleOrderings:
        score = 0
        for sentenceFragment in orderingOfWords:
            score += calculateScore(ordering, sentenceFragment) 
        permutationScore[ordering] = score   

    bestPossibleOrdering = max(permutationScore, key=permutationScore.get)
    print("HELLO: ", bestPossibleOrdering)

    return bestPossibleOrdering

    # [(sergey, brin), (brin, was), (was, born), (born, in)]

    # [("sergey", "was", "born", "in", "1950", "Mr.", "Brin", "was" "studying"..)] 

    # sizeOfNewQuery = len(user_query) + len(new_words)
    # for sentenceFragment in orderingOfWords:
    #     splittedSentence = sentenceFragment.split()
    #     possibleWordPairs = find_ngrams(splittedSentence, sizeOfNewQuery)
    #     for pair in possibleWordPairs:
    #         if ()

    # #     if (" ".join([user_query] + new_words) in sentenceFragment):
            

def calculateScore(ordering, sentenceFragment):
    words = sentenceFragment.split()
    score = 0
    last_index = -1

    for word in ordering:
        index = -1
        for i, w in enumerate(words):
            if (word.lower() == w.lower()):
                index = i
                break
        if index == -1:
            return score
        if index <= last_index:
            return score
        
        last_index = index
    
    score += 1
    return score
    
            

def find_ngrams(input_list, n):
  return zip(*[input_list[i:] for i in range(n)])


def remove_plural_and_singular(words, target_word):
    """
    Removes the plural and singular versions of a target word from a list of words.

    Args:
    - words: a list of words
    - target_word: the target word to check against

    Returns:
    - A modified list of words with plural and singular versions of the target word removed
    """
    # Create a copy of the input list to avoid modifying it directly
    new_words = words.copy()

    # Iterate over each word in the list
    for word in words:
        # Check if the word is a plural or singular version of the target word
        if word == make_plural(target_word) or word == target_word:
            # If it is, remove it from the new list
            new_words.remove(word)

    # Return the modified list
    return new_words

def make_plural(word):
    """
    Returns the plural version of the given word.
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
    # Add "s" to the end of the word in all other cases
    else:
        return word + "s"