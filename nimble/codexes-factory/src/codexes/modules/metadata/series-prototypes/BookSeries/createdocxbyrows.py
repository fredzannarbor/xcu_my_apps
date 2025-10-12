import datetime
import json
import re
from pathlib import Path

import pandas as pd

try:
    from pypandoc import convert_file
except ImportError as e:
    print("Pandoc not installed. No pypandoc module")
    print(e)

import streamlit as st
from docx import Document


# this function
def metadatas2docx(metadatas, thisdoc_dir, target_df="LSI"):
    # create a dataframe from the metadatas
    print(">entering metadatas2df")
    # print('metadata keys', metadatas.keys())
    # apply regex to the values in the metadatas dict
    for k, v in metadatas.items():
        if isinstance(v, str):
            metadatas[k] = re.sub(r'^\n+', '', v)


    if metadatas['mode'] == "assess":
        return
    if target_df == "LSI":
        # initializing variables

        ISBN = str(metadatas['ISBN'])
        metadatas["AI_byline"] = "Enhanced by Nimble Books AI"
        copyright_credit_pd = "(c) " + str(datetime.datetime.now().year) + " " + metadatas["publisher"]
        metadatas['foreword_sig'] = "Cincinnatus [AI]"  # replace with varaib le
        foreword_sig_line = "--" + metadatas['foreword_sig']

        tldr1_text = metadatas["TLDR (one word)"][1]
        tldr_vanilla_text = metadatas["TLDR"][1]
        ELI5_text = metadatas["ELI5"][1]

        title = {"string": metadatas['title'], "style": "Title Page Title"}
        if metadatas["subtitle"]:
            subtitle = {"string": metadatas["subtitle"], "style": "Title Page Subtitle"}
        else:
            subtitle = {"string": "TK", "style": "Title Page Subtitle"}

        byline = {"string": metadatas["author"], "style": "Title Page Byline"}

        AI_byline = {"string": metadatas["AI_byline"], "style": "Title Page Byline"}
        imprint = {"string": metadatas["imprint"], "style": "Title Page Nimble Logotype"}
        pagebreak = {"string": "Page Break", "style": "Page Break"}
        publishing_information = {"string": "Publishing Information", "style": "Heading 2"}
        copyright_line = {"string": copyright_credit_pd, "style": "Body Text - flush left"}
        if ISBN:
            ISBN_line = {"string": "ISBN: " + str(metadatas['ISBN']), "style": "Body Text - flush left"}
        else:
            metadatas["ISBN"] = "TK"
            ISBN_text = "ISBN: " + metadatas['ISBN']
            ISBN_line = {"string": ISBN_text, "style": "Body Text - flush left"}
        series_name = "AI Lab for Book-Lovers "
        series_number = "No. "  # metadatas["series_number"]
        series_name_line = {"string": series_name, "style": "Body Text - flush left"}
        series_number_line = {"string": series_number, "style": "Body Text - flush left"}
        series_info_text = "Humans and AI making books richer, more diverse, and more surprising."
        series_info_line = {"string": series_info_text, "style": "Body Text - flush left"}
        bibliographic_kw = {"string": "Bibliographic Keywords", "style": "Heading 2"}
        if iter(metadatas['Publisher-supplied Keywords']):
            author_supplied_kw_string = ', '.join(metadatas['Publisher-supplied Keywords'])
            author_supplied_kw_heading = {"string": "Publisher-supplied Keywords", "style": "Heading 2"}
            author_supplied_kw_line = {"string": author_supplied_kw_string, "style": "Heading 2"}
        else:
            author_supplied_kw_heading = {"string": "", "style": ""}
            author_supplied_kw_line = {"string": "", "style": ""}
        algorithmically_generated_kw_line = {"string": "AI-generated Keyword Phrases", "style": "Heading 2"}
        algorithmically_generated_kw = {"string": metadatas["Bibliographic Keyword Phrases"],
                                        "style": "Body Text - flush left"}

        pagebreak3 = {"string": "Page Break", "style": "Page Break"}
        foreword_line = {"string": "Foreword", "style": "Heading 1"}
        foreword = {"string": metadatas["Foreword"], "style": "Body Text"}
        foreword_sig = {"string": metadatas["foreword_sig"], "style": "Signature"}
        abstracts = {"string": "Abstracts", "style": "Heading 1"}
        scientific_style = {"string": "Scientific Style", "style": "Heading 2"}
        scientific_style_text = {"string": metadatas["Scientific Style"][1], "style": "Body Text"}

        tldr1_heading = {"string": "TL;DR (one word)", "style": "Heading 2"}
        tldr1_line = {"string": tldr1_text, "style": "Body Text"}
        tldr_vanilla = {"string": "TL;DR (vanilla)", "style": "Heading 2"}
        tldr_vanilla_line = {"string": tldr_vanilla_text, "style": "Body Text"}
        ELI5 = {"string": "Explain It To Me Like I'm Five Years Old", "style": "Heading 2"}
        ELI5_line = {"string": ELI5_text, "style": "Body Text"}
        pagebreak5 = {"string": "Page Break", "style": "Page Break"}
        viewpoints_heading = {"string": "Viewpoints", "style": "Heading 1"}
        viewpoints_motivation = {"string": "These perspectives increase the reader's exposure to viewpoint diversity.",
                                 "style": "Body Text"}
        MAGA_heading = {"string": "MAGA Perspective", "style": "Heading 2"}
        MAGA_text = {"string": metadatas["Hostile MAGA Perspective"][1], "style": "Body Text"}
        FormalDissent_heading = {"string": "Formal Dissent", "style": "Heading 2"}
        FormalDissent_text = {"string": metadatas["Formal Dissent"][1], "style": "Body Text"}
        RedTeamCritique_heading = {"string": "Red Team Critique", "style": "Heading 2"}
        RedTeamCritique_text = {"string": metadatas["Red Team Critique"][1], "style": "Body Text"}
        ActionItems_heading = {"string": "Action Items", "style": "Heading 2"}
        ActionItems_text = {"string": metadatas["Suggested Action Items"][1], "style": "Body Text"}
        pagebreak4 = {"string": "Page Break", "style": "Page Break"}
        recursive_headings = {"string": "Summaries", "style": "Heading 1"}
        recursive_methods_heading = {"string": "Methods", "style": "Heading 2"}
        recursive_methods_text = {"string": metadatas["Methods"], "style": "Body Text"}
        extractive_summary_heading = {"string": "Extractive Summary", "style": "Heading 2"}
        extractive_summary_signature = {
            "string": "Most representative sentences identified by sumy implementation of LexRank algorithm.",
            "style": "Signature"}
        extractive_summary_text = {"string": metadatas["extractive_summary"], "style": "Body Text"}
        extractive_synopsis_heading = {"string": "Extractive Synopsis", "style": "Heading 2"}
        extractive_synopsis_signature = {
            "string": "Most representative several sentences identified by sumy implementation of LexRank algorithm.",
            "style": "Signature"}
        extractive_synopsis_text = {"string": metadatas["extractive_synopsis"], "style": "Body Text"}
        # add all dicts to a list
        rows = [title, subtitle, byline, AI_byline, imprint, pagebreak, publishing_information, copyright_line,
                ISBN_line, series_name_line, series_number_line, series_info_line,
                bibliographic_kw, author_supplied_kw_heading, author_supplied_kw_line,
                algorithmically_generated_kw_line,
                algorithmically_generated_kw, pagebreak3, foreword_line, foreword, foreword_sig, abstracts,
                scientific_style,
                scientific_style_text, tldr1_heading, tldr1_line,
                tldr_vanilla, tldr_vanilla_line, ELI5, ELI5_line, ActionItems_heading, ActionItems_text, pagebreak5,
                viewpoints_heading, viewpoints_motivation, FormalDissent_heading,
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
                pagesubhead = "Page " + str(pagepair[0])
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


def metadatas2bookjson(metadatas, thisdoc_dir, distributor="LSI"):
    # convert the metadata to a json file
    bookjson = {}
    bookjson["BookTitle"] = metadatas["title"]
    bookjson["SubTitle"] = metadatas["subtitle"]
    bookjson["Byline"] = metadatas["author"]
    bookjson["ImprintText"] = metadatas["imprint"]
    bookjson["ImageFileName"] = ""  # metadatas["cover_image"]
    bookjson["settings"] = "default"
    bookjson["distributor"] = "LSI"
    bookjson["InvertedColor"] = "White"
    bookjson["DominantColor"] = "Nimble Maroon"
    bookjson["BaseFont"] = "Skolar PE Regular"
    bookjson["trimsizewidth"] = 8.5  # metadatas["trim_size"][0]
    bookjson["trimsizeheight"] = 11  # metadatas["trim_size"][1]
    bookjson["spinewidth"] = "1.0"  # metadatas["spine_width"]
    print(metadatas["Recursive Summaries"][-1])
    print(metadatas["Publisher-supplied synopsis"])
    backtext = metadatas["Recursive Summaries"][-1] + metadatas["Publisher-supplied synopsis"]
    bookjson["backtext"] = metadatas["Recursive Summaries"][-1]
    st.write(bookjson)
    with open(thisdoc_dir + '/' + Path(thisdoc_dir).stem + "_book.json", 'w') as f:
        json.dump(bookjson, f)

    with open("bookjsonfiles/" + Path(thisdoc_dir).stem + "_book.json", 'w') as f:
        json.dump(bookjson, f)

    return bookjson


def metadatas2internationaledition(metadatas, thisdoc_dir, languages, international_presets, edition_name):
    # convert

    # add bespoke content that motivatess the international edition

    # translate selected metadata to other languages
    international_text = 'placeholder'  # hgrtext2googlecloudtranslate.py(metadatas, languages, international_presets)
    # assemble supplementary front matter section

    return "successfully built book json file for Scribus"
