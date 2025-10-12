file = 'working/contracted/15_with_author/AGFW/list2.txt'
import csv
# read file as list of lists
with open(file, 'r') as f:
    search_terms_list = f.read().splitlines()

list = [['Sherlock Holmes', 'Sherlock', 'Holmes'], ['John Watson MD', 'Watson', 'Dr. Watson']]


with open("out.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(list)