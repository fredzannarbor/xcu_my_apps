from nltk.tokenize import MWETokenizer
tokenizer = MWETokenizer()
tokenizer.add_mwe(('AKAGI', 'MARU'))
result = tokenizer.tokenize('Something about AKAGI MARU'.split())
print(result)

