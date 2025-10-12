
'''
This module contains the function that converts a dictionary of strings and styles into a docx file.

'''
import pandas as pd

def metadatas2docx(contentdicts_list, thisdoc_dir, target_df="LSI"):
    # read list of dicts into a dataframe
    df = pd.DataFrame(contentdicts_list)
    df.set_index("key")
   # create a list of dicts for each row

        rows = [title, subtitle, byline, AI_byline, imprint, pagebreak, publishing_information, copyright_line,
                ISBN_line, series_name_line, series_number_line, series_info_line,
                bibliographic_kw, author_supplied_kw_heading, author_supplied_kw_line, algorithmically_generated_kw_line,
                algorithmically_generated_kw, pagebreak3, foreword_line, foreword, foreword_sig, abstracts,
                scientific_style,
                scientific_style_text, tldr1_heading, tldr1_line,
                tldr_vanilla, tldr_vanilla_line, ELI5, ELI5_line, ActionItems_heading, ActionItems_text, pagebreak5, viewpoints_heading, viewpoints_motivation, FormalDissent_heading,
                FormalDissent_text, RedTeamCritique_heading, RedTeamCritique_text, MAGA_heading, MAGA_text,
                pagebreak4, recursive_headings,
                recursive_methods_heading,
                recursive_methods_text]
        recursive_rows = []

        for index, r in enumerate(metadatas["Recursive Summaries"]):
            recursive_summaries_heading = {"string": "Recursive Summary Round " + str(index), "style": "Heading 2"}
            recursive_rows.append(recursive_summaries_heading)
            recursive_summaries_text = {"string": r, "style": "Body Text"}
            recursive_rows.append(recursive_summaries_text)
        rows.extend(recursive_rows)

        if metadatas["page_by_page_results"]:
            pagebypage_rows = []
            pagebypage_page_heading = {"string": "Page by Page Summaries ", "style": "Heading 2"}
            pagebypage_rows.append(pagebypage_page_heading)
            pagesummaries = metadatas["page_by_page_results"]

            for pagepair in pagesummaries:
                pagesubhead =  "Page " + str(pagepair[0])
                pagetext_pp = re.sub(r'^\n\n', '', pagepair[1])
                pageheading = {"string": pagesubhead, "style": "Heading 3"}
                pagetext = {"string": pagetext_pp, "style": "Body Text"}
                pagebypage_rows.append(pageheading)
                pagebypage_rows.append(pagetext)
            rows.extend(pagebypage_rows)

        if metadatas['Text2Image Prompt']:
            imageprompt_rows = []
            pagebreak5 = {"string": "Page Break", "style": "Page Break"}
            imageprompt_heading = {"string": "Moods", "style": "Heading 1"}
            imageprompt_rows.append(imageprompt_heading)
            image_placeholder = {"string": "Image Placeholder", "style": "Image"}
            imageprompt_rows.append(image_placeholder)
            imageprompt_text = {"string": metadatas['Text2Image Prompt'], "style": "Caption"}
            imageprompt_rows.append(imageprompt_text)
            rows.extend(imageprompt_rows)

        if metadatas['Text2Image Prompt (Stable Diffusion)']:
            imageprompt_rows = []
            imageprompt_heading = {"string": "Moods", "style": "Heading 1"}
            imageprompt_rows.append(imageprompt_heading)
            image_placeholder = {"string": "Image Placeholder", "style": "Image"}
            imageprompt_rows.append(image_placeholder)
            imageprompt_text = {"string": metadatas['Text2Image Prompt (Stable Diffusion)'], "style": "Caption"}
            imageprompt_rows.append(imageprompt_text)
            rows.extend(imageprompt_rows)

        with open(thisdoc_dir + '/rows.json', "w") as f:
            json.dump(rows, f)

        # create a dataframe from a list of strings

        docx_production_df = pd.DataFrame(rows)
        docx_production_df.to_json(thisdoc_dir + '/' + "target_df.json")

        document = Document("resources/docx/FrontMatter2.docx")
        try:
            for index, row in docx_production_df.iterrows():
                for line in row["string"].splitlines():
                    if row["style"] == "Page Break":
                        document.add_page_break()
                        continue
                    document.add_paragraph(line, row["style"])
        except Exception as e:
            errmessage = str(e) + 'error in creating word doc'
            print(errmessage)
        document.save(thisdoc_dir + '/' + "frontmatter.docx")

        # convert the doc to pdf
        try:
            convert_file(thisdoc_dir + '/' + "frontmatter.docx", 'pdf',
                              outputfile=thisdoc_dir + '/' + "frontmatter.pdf")
        except Exception as e:
            errmessage = str(e) + 'error in creating interior postscript'
            print(errmessage)

        return docx_production_df, document

