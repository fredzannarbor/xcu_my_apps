import pandas as pd
from pandas_profiling import ProfileReport

df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
profile = ProfileReport(df)

'''
https://stackoverflow.com/questions/70908256/how-to-fix-this-error-while-using-pandas-profiling-in-jupyter-notebook
If you are getting the same traceback I'm getting where this error occurs in pandas_profiling.model.pandas.utils_pandas, you should be able to fix this by changing:

w_median = data[weights == np.max(weights)][0]

to

w_median = data[np.where(weights == np.max(weights))][0]

In the weighted_median function in $(YOUR_VIRTUAL_ENVIRONMENT_OR_PYTHON_DIR)/lib/python$(PYVERSION)/site-packages/pandas-profiling/model/pandas/utils_pandas.py

(line 13 for pandas-profiling version 3.1.0)

'''