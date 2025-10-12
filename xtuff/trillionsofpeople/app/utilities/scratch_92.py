import pandas as pd

metadatas = pd.read_json('output/Logan3pp/metadatas_df.json')
print(metadatas)
print(metadatas['Text2MoodImagePrompt_response'])
#print(metadatas)
if metadatas['Text2MoodImagePrompt_response'] is not None:
    # get images`
    count = 0
    d = metadatas['Text2MoodImagePrompt_response'].iloc[0]
    print(d)
    for item in d["data"]:
        #print(item)
        url = item["url"]
        print(url)