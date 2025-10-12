# -*- coding: utf-8 -*-
# script to convert docx to text chunks of arbitrary size

import argparse
import os

import docx
from nltk.tokenize import sent_tokenize

from app.utilities.utilities import create_safe_dir_from_file_path


def chunkize(docxfile, output_dir, chunksize=400):
    doc2 = docx.Document(docxfile)
    chunk_no = 0
    data = []
    prompt = []
    chunk_list = []
    chunk = ''
    d = {}
    total_words, words_in_chunk = 0, 0

    for para in doc2.paragraphs:
        tokenized_para = sent_tokenize(para.text)
        
        paragraph_so_far = ""
        for sentence in tokenized_para:
            words_in_sentence = len(sentence.split()) 
            words_in_chunk = words_in_chunk + words_in_sentence
            if words_in_chunk >= chunksize:
                chunk = chunk + paragraph_so_far
                chunk_list.append(chunk)
                chunk = ''
                chunk_no = chunk_no + 1
                total_words += words_in_chunk
                words_in_chunk = 0
            paragraph_so_far = paragraph_so_far + sentence
        chunk = chunk + '\n' + para.text

    chunk_list.append(chunk)

    print('chunked', docxfile, 'with ', total_words, 'total words into', len(chunk_list), 'chunks','\n')
    safenames = create_safe_dir_from_file_path(docxfile, output_dir)
    thisdoc_dirname = safenames[0]
    thisdoc_basename = safenames[1]
    thisdoc_chunk_path = os.path.join(thisdoc_dirname + '/' + thisdoc_basename + '._chunks.txt')
    with open(thisdoc_chunk_path, 'w') as f:
        for item in chunk_list:
            f.write("%s\n" % item)

    return thisdoc_chunk_path, chunk_list
    


def argparse_handler():
    argparser = argparse.ArgumentParser()
  
    argparser.add_argument('--docxfile', help='path to docx file', default='test/docx/lorem.docx')
    argparser.add_argument('--paras_limit', help='limit number of paragraphs displayed on return', default=20)
    argparser.add_argument('--output_dir', help='path to output directory', default='output')
    argparser.add_argument('--list2string', help='output converted text as single string, not a list', default=False)
    
    args = argparser.parse_args()
    docxfile = args.docxfile
    paras_limit = args.paras_limit
    output_dir = args.output_dir
    list2string = args.list2string
    
    return docxfile, paras_limit, output_dir,list2string


if __name__ == "__main__":
    
    docxfile, paras_limit, output_dir, list2string = argparse_handler()
    text = chunkize(docxfile, output_dir)
    #print(text[:paras_limit])