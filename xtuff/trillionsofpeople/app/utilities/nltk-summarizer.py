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
import pandas as pd
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize import sent_tokenize, word_tokenize


def summarize(infile, ratio, word_count):
    # detect the encoding for infile
    file_encoding = chardet.detect(
        open(infile, 'rb').read())['encoding']
    print(file_encoding)
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
    sentencesdf = pd.DataFrame(list(nlargest(number_of_sentences, ranking, key=ranking.get)), columns=['Sentence'])
    print(sentencesdf)
    indexes = nlargest(number_of_sentences, ranking, key=ranking.get)
    
  


    print(str([sentences[j] for j in sorted(indexes)]), file=open('../data/output.txt', 'w', encoding='utf-8'))

    return indexes

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='Nimble Standard')
    parser.add_argument('--infile', '-i', type=str, default='../data/input.txt', help="input file")
    parser.add_argument('--outfile', '-o', type=str, default='../data/output.txt', help="output file")
    parser.add_argument('--datadir', '-d', type=str, default='../data', help="data directory")
    parser.add_argument('--tmpdir', '-t', type=str, default='/tmp', help="temporary directory")
    parser.add_argument('--logdir', '-l', type=str, default='../logs', help="log directory")
    #parser.add_argument('--logfile', '-f', type=str, default='nimble.log', help="log file")

    parser.add_argument('--number_of_sentences', '-n', type=int, default=10, help="number of sentences")
    parser.add_argument('--sentence_length', '-s', type=int, default=7, help="only return sentences with greater than this number of words")
  


    args = parser.parse_args()

    infile = args.infile
    outfile = args.outfile
    datadir = args.datadir
    tmpdir = args.tmpdir
    logdir = args.logdir
    #logfile = args.logfile
    number_of_sentences = args.number_of_sentences
    sentence_length = args.sentence_length

    result = summarize(infile, sentence_length, number_of_sentences)


