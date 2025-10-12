
'''
This module contains the function that converts a dictionary of strings and styles into a docx file.

'''
import pandas as pd
import requests
def rows2docx(rows, thisdoc_dir, target_df="LSI"):
    # read list of dicts into a dataframe
    df = pd.DataFrame(contentdicts_list)
    df.set_index("key")
   # create a list of dicts for each row


    document = Document("resources/docx/FrontMatter2.docx")
    try:
        for index, row in df.iterrows():
            for line in row["string"].splitlines():
                if row["style"] == "Page Break":
                    document.add_page_break()
                    continue
                if row["style"] == "Image":
                    # add image from url
                    insert_image = requests.get(line, stream=True)
                    document.add_picture(insert_image", width=Inches(5.5))
                    continue
                document.add_paragraph(line, row["style"])
    except Exception as e:
        errmessage = str(e) + 'error in creating word doc'
        print(errmessage)
    document.save(thisdoc_dir + '/' + "newbook.docx")

    return df, document

