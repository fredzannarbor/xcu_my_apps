import coiled
cluster = coiled.Cluster(n_workers=10)

from dask.distributed import Client
client = Client(cluster)
print('Dashboard:l', client.dashboard_link)
import dask.dataframe as dd
import pandas as pd
import hdfs
def lreadline(inputJsonIterator):
    with hdfs.open(inputJsonIterator,mode='rt') as f:
        lines = f.read().split('\n')
    return line
f = 'enwiki-latest.json'
#wiki_df = dd.read_json(f)
file = lreadline(f)
ddf = dd.from_delayed(file)
ddf.head()


