from gensim import utils
import json
import time

start = time.time()
count = 0

list_to_check = []
with open('app/data/pantheon_all_names.txt', 'r') as f:
    for line in f:
        list_to_check.append(line.strip())
    set_to_check = set(list_to_check)

foundcount = 0  # count of names found in the list
filename = '/Users/fred/unity/trillions-deploy/app/data/enwiki-latest.json.gz'
with utils.open(filename, 'rb') as f:
    for line in f:
        # decode each JSON line into a Python dictionary object
        article = json.loads(line)
        count = count + 1
        if (count % 100000) == 0:
            print(count)
            print(time.time() - start)
        # each article has a "title", a mapping of interlinks and a list of "section_titles" 
        if article['title'] in set_to_check:
            articlefilename = article['title'].replace(" ", "_") + '.json'
            with open(articlefilename, 'w') as f:
                    json.dump(article, f)
            foundcount = foundcount + 1
            if (foundcount % 100) == 0:
                print(foundcount)
                print(time.time() - start)
                # save article to file


            open ('app/data/pantheon_all_names_found.txt', 'a').write(article['title'] + '\n')
            if foundcount > 10:
                break

        #print("Article title: %s" % article['title'])
        # #print("Interlinks: %s" + article['interlinks'])
        # for section_title, section_text in zip(article['section_titles'], article['section_texts']):
        #     print("Section title: %s" % section_title)
        #     print("Section text: %s" % section_text)