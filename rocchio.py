import math
from collections import defaultdict

alpha = 1
beta = 0.5
gamma = 0.5


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
        term1 = (alpha * q0[word])
        if (word in relevant_docs.keys() and relevant_docs[word] >= 1):
            term2 = beta * (term_weights[word] / R)
        else:
            term2 = 0
        
        if (word in irrelavant_docs.keys() and irrelavant_docs[word] >= 1):
            term3 = gamma * (term_weights[word] / NR)
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

