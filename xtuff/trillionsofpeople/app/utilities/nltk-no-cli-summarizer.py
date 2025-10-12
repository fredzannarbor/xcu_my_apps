"""
Python
Read in the file '../data/input.txt'.
Filter out sentences shorter than seven words long.
Treat new line characters as sentence breaks.
Extract the ten most representative sentences.
"""

from collections import defaultdict
from heapq import nlargest

import chardet
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize import sent_tokenize, word_tokenize

infile = '../data/input.txt'
sentence_length = 7
number_of_sentences = 10

# detect the encoding for infile
file_encoding = chardet.detect(
    open(infile, 'rb').read())['encoding']
print(file_encoding)
file_encoding = 'cp437'
# read in the file with encoding = file_encoding
with open(infile, encoding=file_encoding, errors="ignore") as f:
    text = f.read()

# Filter out sentences shorter than specified length.
sentences = sent_tokenize(text)
sentences = [sentence for sentence in sentences if len(sentence) > sentence_length]

# Filter out very long sentences.
sentences = [sentence for sentence in sentences if len(sentence) < 150]


# Filter out sentences that are actually part of the table of contents
sentences = [sentence for sentence in sentences if not sentence.startswith('CONTENTS')]

# Treat new line characters as sentence breaks.
sentences = [sentence.replace('\n', ' ') for sentence in sentences]

# Extract the most representative sentences.
words = [word_tokenize(sentence) for sentence in sentences]
words = [word for sentence in words for word in sentence]
words = [word.lower() for word in words]
words = [word for word in words if word not in stopwords.words('english')]
words = [word for word in words if word.isalpha()]

frequencies = FreqDist(words)

ranking = defaultdict(int)

for i, sentence in enumerate(words):
    for word in word_tokenize(sentence):
        if word in frequencies:
            ranking[i] += frequencies[word]


#print(sentences)
# returns sentences in descending order of ranking

indexes = nlargest(number_of_sentences, ranking, key=ranking.get)

print(str([sentences[j] for j in sorted(indexes)]))

#print(str([sentences[j] for j in sorted(indexes)]), file=open('../data/output.txt', 'w', encoding='utf-8'))





