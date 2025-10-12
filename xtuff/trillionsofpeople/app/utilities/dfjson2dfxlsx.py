# reads json, emits xlsx
import pandas as pd 
filename = 'resources/json/BIP_truth_master_LSI_KDP_forthcoming.json'
df = pd.read_json(filename)
df['Pub Date'] = pd.to_datetime(df['Pub Date'])
df.to_excel('resources/json/BIP_truth_master_LSI_KDP_test.xlsx')

