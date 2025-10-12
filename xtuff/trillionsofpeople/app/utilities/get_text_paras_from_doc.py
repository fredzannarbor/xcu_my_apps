# -*- coding: utf-8 -*-
# script to convert OpenAI OpenaI Python preset files to
# an extended JSON format

import docx
from simplify_docx import simplify

doc = docx.Document("/Users/fred/bin/nimble/openai/nimbleAI/uploads/Granddaughter_Project_-_Final_1.docx")

my_doc_as_json = simplify(doc)

print(my_doc_as_json)

# chunk_no = 0
# data = []
# prompt = []
# chunk = ''

# words_in_chunk = 0

# sample = open('samplefile.txt', 'w') 

# for para in doc.paragraphs:

#     #print(para.text, file = sample)
#     print(para.text, '\n')
#     words_in_para = len(para.text.split()) 
#     words_in_chunk = words_in_chunk + words_in_para

#     if words_in_chunk >= 1000:
#         print(chunk)
#         print('---', '\n', 'chunk no:', chunk_no, 'words in chunk:', words_in_chunk)
#         prompt = []
#         chunk = ''
#         chunk_no = chunk_no + 1
#         words_in_chunk = 0
    
# print(prompt)
#     #data.append(prompt)
    