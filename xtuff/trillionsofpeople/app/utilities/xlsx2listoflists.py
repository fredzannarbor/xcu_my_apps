

import pandas as pd

filename = '/Users/fred/unity/app/userdocs/37/LeoBloom/kdp_author_ids.xlsx'


df = pd.read_excel(filename, sheet_name='kdp_author_ids')

def convert_to_list_of_lists(df):
    df_list = df.values.tolist()
    df_list_of_lists = []
    for i in range(len(df_list)):
        if i == 0:
            df_list_of_lists.append([df_list[i][0], [df_list[i][1]]])
        elif df_list[i][0] == df_list[i-1][0]:
            df_list_of_lists[-1][1].append(df_list[i][1])
        else:
            df_list_of_lists.append([df_list[i][0], [df_list[i][1]]])
    return df_list_of_lists

df_list_of_lists = convert_to_list_of_lists(df)
print(df_list_of_lists)