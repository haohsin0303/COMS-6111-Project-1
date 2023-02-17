import math
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer

ALPHA = 1
BETA = 0.75
GAMMA = 0.15

Q0 = 0
R, NR, SUM_R, SUM_NR = 0, 0, 0, 0

def createTfIdf():
    return TfidfVectorizer(analyzer="word", stop_words='english')

def transformUserQueryToVector(tf_idf, search_results, user_query):
    global Q0
    tf_idf.fit_transform([result for result in search_results ])
    Q0 = tf_idf.transform(user_query)

def transformDocumentToVector(tf_idf, search_results, relevancy_doc ):
    tf_idf.fit_transform([result for result in search_results ])
    result = []
    for d in relevancy_doc:
        result.append(tf_idf.transform([d]))
    return result
    
def setRocchioParams(relevant_documents, irrelevant_documents):
    global R, NR, SUM_R, SUM_NR
    R, NR = len(relevant_documents), len(irrelevant_documents)
    SUM_R, SUM_NR = sum(relevant_documents), sum(irrelevant_documents)


def runRocchio():
    global ALPHA, BETA, GAMMA, R, NR, SUM_R, SUM_NR
    print("Alpha:", ALPHA)
    print("Beta: ", BETA)
    print("GAMMA: ", GAMMA)
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
    return highest_words[:2]








def tf_idf_weighting(term_freq, relevant_doc_freq, irrelevant_doc_freq):
    N = 10
    term_weights = defaultdict(int)
    for word in relevant_doc_freq:
        tf = term_freq[word]
        df = relevant_doc_freq[word] + irrelevant_doc_freq[word]

        term_weights[word] = tf * math.log(N / df)

    return term_weights


def run_rocchio(q0, relevant_docs, irrelavant_docs, term_weights, R, NR):
    new_q = {}
    for word in q0:
        term1 = (ALPHA * q0[word])
        if (word in relevant_docs.keys() and relevant_docs[word] >= 1):
            term2 = BETA * (term_weights[word] / R)
        else:
            term2 = 0
        
        if (word in irrelavant_docs.keys() and irrelavant_docs[word] >= 1):
            term3 = GAMMA * (term_weights[word] / NR)
        else:
            term3 = 0

        new_q[word] = term1 + term2 - term3

    return new_q


def select_highest_valued_words(q, old_query):
    duplicate = set(old_query.split()).intersection(q)
    print("duplicate", duplicate)
    print("q", q)
    print("old_query", old_query)
    for duplicate_key in duplicate: del q[duplicate_key]

    sorted_term_weights = sorted(q.items(), key=lambda x: x[1])
    selected_terms = map(lambda x: x[0], sorted_term_weights[-2:])
  
    return [word for word in selected_terms]

