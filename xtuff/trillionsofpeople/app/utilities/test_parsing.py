import re

import nltk
from mosestokenizer import *
from nltk.tokenize.treebank import TreebankWordDetokenizer

text = '''Japanese  Battleship   NAGATO 
1920
The battleship NAGATO was the first in the world to carry 16in guns. They were arranged in four twin turrets. The secondary armament guns were 5.5in mounted in single casemates. Four 3in AA were also provided along with eight 21in torpedo tubes. She displaced 32,720 tons and could make 26.7 knots on
trials, which made her not only the heaviest armed battleship of the time but easily the fastest. As with many ships of the time, anti-torpedo nets were carried with the booms prominent along each side. The foremast had six legs instead of the usual three. This ship exceeded any in rival navies and was one of the
very reasons why a naval treaty was called for before it caused another naval shipbuilding race as had happened before WW1. Japan was permitted to keep this ship and her sister MUTSU but in return the US Navy was allowed to match them with the two Colorado class ships of similar size and armament. She
was completed in Kure grey with polished wood decks. The main mast was black from the searchlight platform upward. This ship had mixed firing, using coal and oil.'''


result = ""
tokens = nltk.sent_tokenize(text)
print(text)
new_tokens = []
for t in tokens:
    print (t, "\n")
    t = re.sub('([a-z])\n([a-z])', '\\1 \\2', t)
    new_tokens.append((t))
print('-----------------')
print(new_tokens)
final_text = TreebankWordDetokenizer().detokenize(new_tokens)
print(final_text)

