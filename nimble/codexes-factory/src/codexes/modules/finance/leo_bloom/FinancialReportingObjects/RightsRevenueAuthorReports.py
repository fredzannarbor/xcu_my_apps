import os
import pypandoc
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import load_spreadsheet

"""
This class handles rights revenue received.
The data is in this format:

Title,ISBN,Author ,Author code,Purchaser contact,Purchaser organization,Rights purchased,Fee,Term,Date
RAGING TWENTIES,,Escobar,,Anastasia Gesheva,Postscriptum,Bulgarian,$500 ,7 years,2/7/24

the class is a subclass of FinancialReportingObjects
The class should be able to generate reports in markdown and PDF by author, market, and date signed/expires
"""
import streamlit as st
import pandas as pd
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects


class RightsRevenues(FinancialReportingObjects):

    def __init__(self, parent_instance, file_path=None):
        super().__init__(parent_instance.root)
        if file_path is None:
            file_path = parent_instance.rights_revenue_file_path
        self.rights_revenue_file_path= file_path
        self.dataframe = load_spreadsheet(self.rights_revenue_file_path)
        self.dataframe = self.check_if_rights_dataframe_is_valid()
        self.dataframe = self.dataframe.astype(
            {"ISBN": str, "Author Name": str, "Author code": str, "Purchaser contact": str, "Purchaser organization": str, "Rights purchased": str, "Net Compensation": float, "Term": str, "Date": str, "Author Share": float, "Due to Author": float})

        self.clean_up_rights_revenue()

    def check_if_rights_dataframe_is_valid(self):
        current_columns = self.dataframe.columns.to_list()
        desired_columns = ["Title", "ISBN", "Author Name", "Author code", "Purchaser contact", "Purchaser organization", "Rights purchased", "Net Compensation", "Term", "Date", "Author Share", "Due to Author"]
        # check if current_columns and desired columns are the same

        if not all(col in current_columns for col in desired_columns):
            raise ValueError(f"Invalid columns in rights revenue dataframe {self.rights_revenue_file_path}, revise the data.")
        else:
            print("Rights revenue dataframe is valid")
            return self.dataframe

    def clean_up_rights_revenue(self):
        # remove commas from Fee column

        # convert Date column to datetime
        self.dataframe['Date'] = pd.to_datetime(self.dataframe['Date'])
        # fill NaN values in ISBN column with empty string
        self.dataframe['ISBN'] = self.dataframe['ISBN'].fillna('')

    def _generate_markdown_content_for_rights(self, authors=None, per_author_page=True):
        content = []
        filtered_df = self.dataframe if authors is None or 'all' in (authors if isinstance(authors, list) else [authors]) else self.dataframe[self.dataframe['Author Name'].isin(authors)]

        for author, author_group in filtered_df.groupby('Author Name'):
            author_content = [f"### {author}"]

            for title, group in author_group.groupby('Title'):
                author_content.append(f"#### {title}")

                # Create table header including ISBN above the table
                isbn_md = "\n**ISBN:** "
                for _, row in group.iterrows():
                    isbn_md += f"{row['ISBN']}, "
                isbn_md = isbn_md.rstrip(', ') + "\n"

                # Table construction with modified columns
                table_md = "\n| Contract Date |  Term  | Purchaser | Rights Purchased | Advance | Author Share | Due to Author |\n"
                table_md += "|--------------|--------|-----------|-----------------|---------|--------------|---------------|\n"  # Alignment row

                for _, row in group.iterrows():
                    date_formatted = row['Date'].strftime('%Y-%m-%d')
                    table_md += f"| {date_formatted} | {row['Term']} | {row['Purchaser organization']} | {row['Rights purchased']} | ${row['Net Compensation']:.2f} | {row['Author Share']:.2%} | ${row['Due to Author']:.2f} |\n"

                author_content.append(isbn_md + table_md)

            # Sum up total net compensation
            total_compensation = author_group['Due to Author'].sum()
            author_content.append(f"**Total Due to {author}:** ${total_compensation:.2f}\n")

            if per_author_page:
                content.append("\n".join(author_content + ["\n\\newpage\n"]))
            else:
                content.extend(author_content + ["---"])

        return "\n".join(content)

    def _save_to_file(self, markdown_content, per_author_page=False):
        if per_author_page:
            for author, author_content in zip(self.dataframe['Author Name'].unique(), markdown_content.split("\\newpage")):
                file_name = os.path.join("output", f"rights_{author.replace(' ', '_').replace(',', '_').replace('\'', '_')}.md")
                file_name = file_name.replace('..', '.')
                file_name = file_name.replace('__', '_')
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(author_content)
        else:
            with open("rights_revenue_report.md", "w", encoding="utf-8") as f:
                f.write(markdown_content)

    def _save_to_pdf(self, markdown_content, per_author_page=False):
        extra_args=['-V', 'geometry:left=1in,right=0.75in,top=1in,bottom=1in', '-V', 'columns=80' ]
        if per_author_page:
            for author, author_content in zip(self.dataframe['Author Name'].unique(), markdown_content.split("\\newpage")):
                file_name = os.path.join("output", f"rights_{author.replace(' ', '_').replace(',', '_').replace('\'', '_')}.pdf")
                file_name = file_name.replace('..', '.')
                file_name = file_name.replace('__', '_')

                try:
                    pypandoc.convert_text(author_content, "pdf", "markdown", outputfile=file_name, extra_args=extra_args)
                    print(f"Successfully created rights revenue report for {author}")
                    st.success(f"Successfully created rights revenue report for {author}")
                except RuntimeError as e:
                    print(f"Error creating PDF for {author}: {e}")
        else:
            try:
                pypandoc.convert_text(markdown_content, "pdf", "markdown", outputfile="rights_revenue_report.pdf", extra_args=extra_args)
                print("Successfully created rights revenue report for all authors")
                st.success("Successfully created rights revenue report for all authors")
            except RuntimeError as e:
                print(f"Error creating PDF: {e}")

    def display_compact_reports_in_browser(self, markdown_content, output_format="streamlit"):
        # remove \\newpage from markdow_conent
        display_markdown = markdown_content.replace("\\newpage", "")
        st.markdown(display_markdown, unsafe_allow_html=True)



