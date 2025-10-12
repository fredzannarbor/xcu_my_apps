# python
from fuzzywuzzy import fuzz


def texts2exactmatch(a,b):
    if a == b:
        return True
    else:
        return False
    
def texts2caseinsensitivematch(a,b):
    if a.lower() == b.lower():
        return True
    else:
        return False
    

def texts2fuzzymatch(a, b, fuzzymatch_threshold=90):
    result = fuzz.ratio(a, b)
    if result >= fuzzymatch_threshold:
        return True, result
    else:
        return False, result
    
def texts2fuzzymatch_partial(a, b, fuzzymatch_threshold=90):
    result = fuzz.partial_ratio(a, b)
    if result >= fuzzymatch_threshold:
        return True
    else:
        return False
    
def texts2fuzzymatch_tokensort(a, b, fuzzymatch_threshold=90):
    result = fuzz.token_sort_ratio(a, b)
    if result >= fuzzymatch_threshold:
        return True
    else:
        return False
    
def texts2fuzzymatch_tokenset(a, b, fuzzymatch_threshold=90):
    result = fuzz.token_set_ratio(a, b)
    if result >= fuzzymatch_threshold:
        return True
    else:
        return False
