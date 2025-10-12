# process ideas stored in cumulative.csv
import pandas as pd
df = pd.read_csv("integrate_ideas/cumulative.csv")
df.info()
print(df.sample(10))
