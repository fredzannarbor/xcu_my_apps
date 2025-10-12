import argparse
import json
import os
import re
from os import path

import fitz
from numeral import int2roman

add_mwe_list = [('ADEN', 'MARU'),('IMPERIAL', 'JAPANESE', 'NAVY'),('AIKOKU', 'MARU'),('AKAGANE', 'MARU'),('AKAGI', 'MARU'),('AKAGISAN', 'MARU'),('AKATSUKI', 'MARU'),('AKEBONO', 'MARU'),('AKI', 'MARU'),('AKITSU', 'MARU'),('ARGENTINE', 'MARU'),('ASAKA', 'MARU'),('ASUKA', 'MARU'),('ATAGO', 'MARU'),('ATAWA', 'MARU'),('AWA', 'MARU'),('AYOTOSAN', 'MARU'),('BANGKOK', 'MARU'),('BANRYU', 'MARU'),('BRISBANE', 'MARU'),('BUENOS', 'AIRES', 'MARU'),('BUSHO', 'MARU'),('CHIGUSA', 'MARU'),('CHIRYU', 'MARU'),('CHOHAKUSAN', 'MARU'),('CHOJUSAN', 'MARU'),('CHOJUSON', 'MARU'),('CHOSA', 'MARU'),('CHOSHUN', 'MARU'),('EDOGAWA', 'MARU'),('FUKKEN', 'MARU'),('FUKUKEN', 'MARU'),('GENYO', 'MARU'),('GOKOKU', 'MARU'),('GYOKU', 'MARU'),('GYOTEN', 'MARU'),('HAKUREI', 'MARU'),('HAKUSA', 'YAMABIKO', 'MARU'),('HEINAN', 'MARU'),('HIROKAWA', 'MARU'),('HIROMIYA', 'MARU'), ('HITACHI', 'MARU'),('HOFOKU', 'MARU'),('HOFUKU', 'MARU'),('HOKKAI', 'MARU'),('HOKOKU', 'MARU'),('HYUGA', 'MARU'),('ICHIYO', 'MARU'),('ITSUKUSHIMA', 'MARU'),('IZUMO', 'MARU'),('KAGU', 'MARU'),('KAHOKU', 'MARU'),('KAMIKAWA', 'MARU'),('KAMOGAWA', 'MARU'),('KANAN', 'MARU'),('KASHIWARA', 'MARU'),('KASUGA', 'MARU'),('KATSURIKI', 'MARU'),('KAZAN', 'MARU'),('KEIYO', 'MARU'),('KENSHIN', 'MARU'),('KENYO', 'MARU'),('KIBITSU', 'MARU'),('KIMIKAWA', 'MARU'),('KINJOSAN', 'MARU'),('KINRYU', 'MARU'),('KINUGAWA', 'MARU'),('KISHU', 'MARU'),('KIYOKAWA', 'MARU'),('KIYOSUMI', 'MARU'),('KOEI', 'MARU'),('KOGANE', 'MARU'),('KOKUYO', 'MARU'),('KOMAHASHI', 'MARU'),('KONGO', 'MARU'),('KONGOSAN', 'MARU'),('KORYU', 'MARU'),('KUMANO', 'MARU'),('KUNIKAWA', 'MARU'),('KYOKUYO', 'MARU'),('MAGANE', 'MARU'),('MAGANE','MARU'),('MAYASAN', 'MARU'),('MELBOURNE', 'MARU'),('MIIKE', 'MARU'),('MINRYO', 'MARU'),('MOGAMIGAWA', 'MARU'),('NAGARA', 'MARU'),('NAKO', 'MARU'),('NARUTO', 'MARU'),('NICHIEI', 'MARU'),('NIGITSU', 'MARU'),('NIHONKAI', 'MARU'),('NIKAWA', 'MARU'),('NIPPON', 'MARU'),('NIPPONKAI', 'MARU'),('NISSHIN', 'MARU'),('NITTA', 'MARU'),('NOHIMA', 'MARU'),('NOJIMA', 'MARU'),('NOSHIRO', 'MARU'),('NOTO', 'MARU'),('OTAKISAN', 'MARU'),('OTOSISAN', 'MARU'),('OTOWASAN', 'MARU'),('OTOWASON', 'MARU'),('OYAMA', 'MARU'),('RIO', 'DE', 'JANEIRO', 'MARU'),('SADO', 'MARU'),('SAGARA', 'MARU'),('SAGARU', 'MARU'),('SAIGON', 'MARU'),('SAKIDO', 'MARU'),('SAKITO', 'MARU'),('SAKURA', 'MARU'),('SAN', 'DIEGO', 'MARU'),('SAN', 'PEDRO', 'MARU'),('SANUKI', 'MARU'),('SANYO', 'MARU'),('SASAGO', 'MARU'),('SEIKO', 'MARU'),('SERIA', 'MARU'),('SETTSU', 'MARU'),('SHIMANE', 'MARU'),('SHINKO', 'MARU'),('SHINKOKU', 'MARU'),('SHINKYO', 'MARU'),('SHINSHU', 'MARU'),('SHIROGANE', 'MARU'),('SHOBU', 'MARU'),('SHOHO', 'MARU'),('SHOSEI', 'MARU'),('SS', 'SUEZ', 'MARU'),('SUEZ', 'MARU'),('SUGURA', 'MARU'),('SYDNEY', 'MARU'),('TAISEI', 'MARU'),('TAKEKAWA', 'MARU'),('TAMAGAWA', 'MARU'),('TATEKAWA', 'MARU'),('TATEYAMA', 'MARU'),('TATSUMIYA', 'MARU'),('TEIYO', 'MARU'),('TENRYO', 'MARU'),('TOBATA', 'MARU'),('TOEI', 'MARU'),('TOHO', 'MARU'),('TOKITSU', 'MARU'),('TOKO', 'MARU'),('TOYAKAWA', 'MARU'),('TOZAN', 'MARU'),('UKISHIMA', 'MARU'),('YAKASUNI', 'MARU'),('YAMABIKO', 'MARU'),('YAMAGIRI', 'MARU'),('YAMASHIO', 'MARU'),('YAMAURA', 'MARU'),('YAMAZUKI', 'MARU'),('YASAKUNI', 'MARU'),('YAWATA', 'MARU'),('YODOGAWA', 'MARU'),('YUHO', 'MARU'),('ZENYO', 'MARU')]

from nltk.tokenize import MWETokenizer
tokenizer = MWETokenizer()
for m in add_mwe_list:
    tokenizer.add_mwe(m)

rule_file_path = "app/data/indexer_settings/wright-rules.json"

def lookahead_find_new_mwes_by_rule(rule_file_path, text):
    lookahead_terms = []
    unique_new_terms =  []

    rules = ["[A-Z]* MARU", "USS [A-Z]{2,}", "HMS [A-Z]{2,}", "IMPERIAL [A-Z]{3,}"]
    print(text)# read in   the rule file
    for rule in rules:
        print(rule)
        result = re.compile(rule).findall(text)
        print('page search result', result)
        if result:
            lookahead_terms.append(result)

        print(lookahead_terms)
    return lookahead_terms
def pdf_pages_containing_index_terms(pdf_file_path, index_term_file_path, pagelimit):

    add_mwe_list = [('ADEN', 'MARU'),('IMPERIAL', 'JAPANESE', 'NAVY'),('AIKOKU', 'MARU'),('AKAGANE', 'MARU'),('AKAGI', 'MARU'),('AKAGISAN', 'MARU'),('AKATSUKI', 'MARU'),('AKEBONO', 'MARU'),('AKI', 'MARU'),('AKITSU', 'MARU'),('ARGENTINE', 'MARU'),('ASAKA', 'MARU'),('ASUKA', 'MARU'),('ATAGO', 'MARU'),('ATAWA', 'MARU'),('AWA', 'MARU'),('AYOTOSAN', 'MARU'),('BANGKOK', 'MARU'),('BANRYU', 'MARU'),('BRISBANE', 'MARU'),('BUENOS', 'AIRES', 'MARU'),('BUSHO', 'MARU'),('CHIGUSA', 'MARU'),('CHIRYU', 'MARU'),('CHOHAKUSAN', 'MARU'),('CHOJUSAN', 'MARU'),('CHOJUSON', 'MARU'),('CHOSA', 'MARU'),('CHOSHUN', 'MARU'),('EDOGAWA', 'MARU'),('FUKKEN', 'MARU'),('FUKUKEN', 'MARU'),('GENYO', 'MARU'),('GOKOKU', 'MARU'),('GYOKU', 'MARU'),('GYOTEN', 'MARU'),('HAKUREI', 'MARU'),('HAKUSA', 'YAMABIKO', 'MARU'),('HEINAN', 'MARU'),('HIROKAWA', 'MARU'),('HIROMIYA', 'MARU'), ('HITACHI', 'MARU'),('HOFOKU', 'MARU'),('HOFUKU', 'MARU'),('HOKKAI', 'MARU'),('HOKOKU', 'MARU'),('HYUGA', 'MARU'),('ICHIYO', 'MARU'),('ITSUKUSHIMA', 'MARU'),('IZUMO', 'MARU'),('KAGU', 'MARU'),('KAHOKU', 'MARU'),('KAMIKAWA', 'MARU'),('KAMOGAWA', 'MARU'),('KANAN', 'MARU'),('KASHIWARA', 'MARU'),('KASUGA', 'MARU'),('KATSURIKI', 'MARU'),('KAZAN', 'MARU'),('KEIYO', 'MARU'),('KENSHIN', 'MARU'),('KENYO', 'MARU'),('KIBITSU', 'MARU'),('KIMIKAWA', 'MARU'),('KINJOSAN', 'MARU'),('KINRYU', 'MARU'),('KINUGAWA', 'MARU'),('KISHU', 'MARU'),('KIYOKAWA', 'MARU'),('KIYOSUMI', 'MARU'),('KOEI', 'MARU'),('KOGANE', 'MARU'),('KOKUYO', 'MARU'),('KOMAHASHI', 'MARU'),('KONGO', 'MARU'),('KONGOSAN', 'MARU'),('KORYU', 'MARU'),('KUMANO', 'MARU'),('KUNIKAWA', 'MARU'),('KYOKUYO', 'MARU'),('MAGANE', 'MARU'),('MAGANE','MARU'),('MAYASAN', 'MARU'),('MELBOURNE', 'MARU'),('MIIKE', 'MARU'),('MINRYO', 'MARU'),('MOGAMIGAWA', 'MARU'),('NAGARA', 'MARU'),('NAKO', 'MARU'),('NARUTO', 'MARU'),('NICHIEI', 'MARU'),('NIGITSU', 'MARU'),('NIHONKAI', 'MARU'),('NIKAWA', 'MARU'),('NIPPON', 'MARU'),('NIPPONKAI', 'MARU'),('NISSHIN', 'MARU'),('NITTA', 'MARU'),('NOHIMA', 'MARU'),('NOJIMA', 'MARU'),('NOSHIRO', 'MARU'),('NOTO', 'MARU'),('OTAKISAN', 'MARU'),('OTOSISAN', 'MARU'),('OTOWASAN', 'MARU'),('OTOWASON', 'MARU'),('OYAMA', 'MARU'),('RIO', 'DE', 'JANEIRO', 'MARU'),('SADO', 'MARU'),('SAGARA', 'MARU'),('SAGARU', 'MARU'),('SAIGON', 'MARU'),('SAKIDO', 'MARU'),('SAKITO', 'MARU'),('SAKURA', 'MARU'),('SAN', 'DIEGO', 'MARU'),('SAN', 'PEDRO', 'MARU'),('SANUKI', 'MARU'),('SANYO', 'MARU'),('SASAGO', 'MARU'),('SEIKO', 'MARU'),('SERIA', 'MARU'),('SETTSU', 'MARU'),('SHIMANE', 'MARU'),('SHINKO', 'MARU'),('SHINKOKU', 'MARU'),('SHINKYO', 'MARU'),('SHINSHU', 'MARU'),('SHIROGANE', 'MARU'),('SHOBU', 'MARU'),('SHOHO', 'MARU'),('SHOSEI', 'MARU'),('SS', 'SUEZ', 'MARU'),('SUEZ', 'MARU'),('SUGURA', 'MARU'),('SYDNEY', 'MARU'),('TAISEI', 'MARU'),('TAKEKAWA', 'MARU'),('TAMAGAWA', 'MARU'),('TATEKAWA', 'MARU'),('TATEYAMA', 'MARU'),('TATSUMIYA', 'MARU'),('TEIYO', 'MARU'),('TENRYO', 'MARU'),('TOBATA', 'MARU'),('TOEI', 'MARU'),('TOHO', 'MARU'),('TOKITSU', 'MARU'),('TOKO', 'MARU'),('TOYAKAWA', 'MARU'),('TOZAN', 'MARU'),('UKISHIMA', 'MARU'),('YAKASUNI', 'MARU'),('YAMABIKO', 'MARU'),('YAMAGIRI', 'MARU'),('YAMASHIO', 'MARU'),('YAMAURA', 'MARU'),('YAMAZUKI', 'MARU'),('YASAKUNI', 'MARU'),('YAWATA', 'MARU'),('YODOGAWA', 'MARU'),('YUHO', 'MARU'),('ZENYO', 'MARU')]    

    index_term_occurrence_dict = {}
    count = 0
    with fitz.open(pdf_file_path) as doc:
        try:
            text = ""

            for count, page in enumerate(doc, 1):
                
                print("converting page", count, "to text")
                text = page.getText()
                print("page converted to text")
                # add_lookaheads = lookahead_find_new_mwes_by_rule((rule_file_path), text)
                # #print("lookahead terms", add_lookaheads)
                # for l in add_lookaheads:
                #     #print(l)
                #     l = tuple(l)
                #     print('tuple is', l)
                tokenizer = MWETokenizer()
                tokenizer.add_mwe(add_mwe_list)
                mwetext = tokenizer.tokenize(text.split())
                print("mwetext", mwetext)
                with open(index_term_file_path, 'r') as f:

                    # consider looping over multi-word terms first to avoid false positives for legitimate single words that are part of multiple word phrases
                    # for example, carrier AKAGI & transport AKAGI MARU
                    # search on AKAGI would bring back references to both ships, which is wrong

                    for line in f:
                        line = line.strip()

                        addentry = []
                        #if re.compile(r'\b({0})\b'.format(line), flags=re.IGNORECASE).search(text):
                        if line in mwetext:

                            if line not in index_term_occurrence_dict:
                                #print("term", line, "not yet in dict")
                                print("line not in dict")
                                # create a new entry for the index term
                                addpage = [count]
                                addentry = {line: addpage}
                                print('line not in dict', addentry)
                            else:
                                # get current entries for index page and add the current page number
                                print("line is already in dict", line)
                                #print("index_term_occurrence_dict", index_term_occurrence_dict)
                                current_pages_found = index_term_occurrence_dict[line]
                                print("current_pages_found", line, current_pages_found)
                                current_pages_found.append(count)
                                addentry = {line: current_pages_found}
                            index_term_occurrence_dict.update(addentry)
                        else:
                            #print("term", line, "not found")
                            # index term not found on page
                            pass
                print("checked page", count, 'for index terms')
                if count == pagelimit:
                    break

        except Exception as e:
            print(e)
            return None
        
    return index_term_occurrence_dict

if __name__ ==  "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument('--pdf_file_path', help='path to pdf file', default="/Users/fred/bin/nimble/unity/app/data/test.pdf")
    argparser.add_argument('--output_dir', help='path to output directory', default='output_dir')
    argparser.add_argument('--pagelimit', help='limit', default=10)
    argparser.add_argument('--index_term_file_path', help='path to index term file', default="/Users/fred/bin/nimble/unity/app/data/index_terms.txt")
    argparser.add_argument('--front_matter_last_page', help='path to index term file', default=12)
    argparser.add_argument('--unnumbered_front_matter_pages', help='list of unnumbered pages in front matter', default=[2])
    args = argparser.parse_args()
    pdf_file_path = args.pdf_file_path
    output_dir = args.output_dir
    # max number of pages in target PDF to process
    pagelimit = args.pagelimit
    # location of text file containing one index term per line=
    index_term_file_path = args.index_term_file_path
    # last roman numbered front matter page, used for offsetting page values
    front_matter_last_page = args.front_matter_last_page
    # list of unnumbered pages in front matter
    # certain pages in front matter are always unnumbered and should not be included
    unnumbered_front_matter_pages = args.unnumbered_front_matter_pages

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    index_dict = pdf_pages_containing_index_terms(pdf_file_path, index_term_file_path, pagelimit)
   # print(index_dict)

    if index_dict:
    # save index_dict to file
        with open(path.join(output_dir, "index_dict.json"), 'w') as f:
            f.write(json.dumps(index_dict, indent=4, sort_keys=True))


        # save index_dict to properly formatted text
        # note first step is to convert from logical page numbers in PDF
        # to physical page numbers as they would be printed in the book
        # this is the *only*output from this program that has printed book style numbering

        # converting from logical to printed book page numbers

        for key, value in index_dict.items():
            #print(key, value)
            for i, page in enumerate(value):
                if page <= front_matter_last_page:
                    if page in unnumbered_front_matter_pages:
                        value[i] = None
                    else:
                        value[i] = int2roman(page).lower()
                else:
                    value[i] = page - front_matter_last_page
            print(key, value)
            index_dict[key] = value
        print(index_dict)

        
        with open(path.join(output_dir, "index_dict.txt"), 'w') as f:
            for key, value in sorted(index_dict.items()):
                pages = ', '.join(str(x) for x in value)
                #print(pages)
                f.write(key + "\t" +  str(pages) + "\n")
    else:
        print("index dictionary is empty, not printing or saving anything")
