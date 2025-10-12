import os

import streamlit as st
import logging
import pandas as pd
import sys
import pypandoc

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.extend([parent_dir, grandparent_dir])

from codexes.modules.finance.leo_bloom.utilities.classes_utilities import configure_logger
import src.classes.FinancialReportingObjects.KDP_Financial_Reporting_Objects as KDPOs



# Configure logger
configure_logger("INFO")
logger = logging.getLogger(__name__)

class KDPAuthorReports(KDPOs.Kindle_Financial_Reporting_Objects):

    def __init__(self, parent_instance, year, kdp_data): # Add year argument
        super().__init__(parent_instance.root)
        self.parent_instance = parent_instance
        self.year = year # Store year
        self.kdp_data = kdp_data # Initialize kdp_data here
        self.dataframe = self.generate_kdp_author_report_df(kdp_data=self.kdp_data) #Pass kdp_data

    def set_kdp_data(self, data):
        self.kdp_data = data


    def generate_kdp_author_report_df(self, authors=None, kdp_data=None, output_format="streamlit"):
        if self.kdp_data.empty or self.kdp_data is None:
            st.error("No KDP data available for report.")
            return
        else:
            self.kdp_data = kdp_data
            df = self.kdp_data.copy()
            st.write(df.head())
        df['author_share'] = 0.3
        df['due2author'] = df[f'USDeq_Royalty'] * df['author_share']
        df['due2author'] = df['due2author'].round(2)
        print(df.shape)
        logging.info(df['Author Name'].unique().tolist())
        if authors is None or 'all' in (authors if isinstance(authors, list) else [authors]): # parameter
            filtered_df = df
        else:
            authors = [authors] if not isinstance(authors, list) else authors
            mask = df['Author Name'].str.contains('|'.join(authors), case=False, na=False)
            filtered_df = df[mask]

        logging.info(f"Shape of filtered_df: {filtered_df.shape}")

        report_data = []
        for author_name, author_group in filtered_df.groupby('Author Name'):
            author_total = 0
            author_group['Row_Type'] = 'Detail'

            report_data.append((author_name, []))
            for title, title_group in author_group.groupby('Title'):
                title_details = title_group[title_group['Row_Type'] == 'Detail'].copy()
                title_subtotal = title_details['due2author'].sum()


                title_details['Net Units'] = title_group['Net Units Sold']
                net_comp_col = f"USDeq_Royalty_{self.year}"
                if net_comp_col in title_group:
                    title_details[net_comp_col] = title_group[net_comp_col] # Correct: Use entire column (Series)
                else:
                    title_details[net_comp_col] = 0.0
                title_details['author_share'] = title_group['author_share']

                # Subtotal row
                title_subtotal_row = pd.DataFrame([{
                    "Title": title, "ASIN/ISBN": "", "Marketplace": "", "Net Units Sold": "",
                    "USDeq_Royalty": "", "author_share": "", "due2author": title_subtotal,
                    "Author Name": author_name, "Row_Type": "Subtotal"
                }])

                report_data[-1][1].extend(title_details.to_dict('records'))
                report_data[-1][1].extend(title_subtotal_row.to_dict('records'))
                author_total += title_subtotal

            # Author total row
            author_total_row = pd.DataFrame([{
                "Title": "Author Subtotal", "ISBN": "", "Marketplace": "", "Net Units Sold": "",
                "USDeq_Royalty": "", "author_share": "", "due2author": author_total,
                "Author Name": author_name, "Row_Type": "Author Subtotal"
            }])

            report_data[-1][1].extend(author_total_row.to_dict('records'))

        gross_total = filtered_df['due2author'].sum().round(2)
        gross_total_row = pd.DataFrame([{
            "Title": "Gross Total", "ISBN": "", "Marketplace": "", "Net Units Sold": "",
            "USDeq_Royalty": "", "author_share": "", "due2author": gross_total,
            "Author Name": "", "Row_Type": "Gross Total"
        }])

        flat_report_data = [item for author, rows in report_data for item in rows]
        flat_report_data.extend(gross_total_row.to_dict('records'))

        return pd.DataFrame(flat_report_data)

    def kdp_author_report_df2format(self, output_format="streamlit", authors=None, per_author_page=False):
        """
        Generate a markdown report from the author report dataframe and handle different output formats.

        :param output_format: Specifies the output format ('streamlit', 'pdf', or 'markdown')
        :param authors: List of authors to filter by, or None for all authors
        :param per_author_page: If True, each author gets their own markdown page and PDF
        :return: None, but handles file creation or display based on output_format
        """
        if self.dataframe.empty:
            st.error("No data available for report.")
            return

        markdown_content = self._generate_markdown_content(authors, per_author_page)

        if output_format == "streamlit":
            st.markdown(markdown_content, unsafe_allow_html=True)
        elif output_format == "pdf":
            self._save_to_pdf(markdown_content, per_author_page)
        elif output_format == "markdown":
            self._save_to_file(markdown_content, per_author_page)

    def _generate_markdown_content(self, authors=None, per_author_page=False):
        content = []
        filtered_df = self.dataframe if authors is None or 'all' in (authors if isinstance(authors, list) else [authors]) else self.dataframe[self.dataframe['Author Name'].isin(authors)]
        print(filtered_df)
        # drop the row where title == "Gross Total"
        filtered_df = filtered_df[filtered_df['Title'] != "Gross Total"]
        for author, author_group in filtered_df.groupby('Author Name'):
            author_content = [f"### {author}"]

            for title, group in author_group.groupby('Title'):
                if title not in ["Author Subtotal", "Gross Total"]:
                    # get transaction type
                    transaction_type = group[group['Row_Type'] == 'Detail']['Transaction Type'].iloc[0]
                    author_content.append(f"#### {title} ~ KDP royalty type: {transaction_type}")

                    # Filter details and round values
                    details = group[group['Row_Type'] == 'Detail'].round(2)

                    # Create table header
                    table_md = "\n| ISBN          | Royalty Date | Marketplace    | Net Units Sold | USDeq Royalty | Author Share | Due to Author |\n" \
                               "|--------------|--------------|-------------|----------------|--------------|--------------|---------------|\n"

                    for _, row in details.iterrows():
                        # Pad ISBN to 14 characters for alignment
                        isbn_padded = row['ASIN/ISBN'].ljust(14)
                        # Center align 'Net Units Sold'
                        net_units_sold = f"{row['Net Units Sold']:.0f}".center(15)
                        # Append row data to the table, formatted for alignment
                        table_md += f"| {isbn_padded} | {row['Royalty Date']} | {row['Marketplace']} | {net_units_sold} | ${row['USDeq_Royalty']:.2f} | {row['author_share']:.2f}% | ${row['due2author']:.2f} |\n"

                    author_content.append(table_md)
                    if not group[group['Row_Type'] == 'Subtotal'].empty:
                        title_subtotal = group[group['Row_Type'] == 'Subtotal']['due2author'].iloc[0]
                        # Correct calculation of title_unit_sales
                        title_unit_sales = details['Net Units Sold'].sum()  # Calculate from details DataFrame
                        author_content.append(f"Net Units Sold:  {title_unit_sales:.0f} | **Subtotal:** ${title_subtotal:.2f}\n") #added .0f

            if not author_group[author_group['Row_Type'] == 'Author Subtotal'].empty:
                author_subtotal = author_group[author_group['Row_Type'] == 'Author Subtotal']['due2author'].iloc[0]
                author_content.append(f"**AUTHOR GRAND TOTAL** via KDP: ${author_subtotal:.2f}\n")


            if per_author_page:

                content.append("\n".join(author_content + ["\n\\newpage\n"]))
            else:
                content.extend(author_content + ["---"])
        print(content)
        if not self.dataframe[self.dataframe['Row_Type'] == 'Gross Total'].empty:
            gross_total = self.dataframe[self.dataframe['Row_Type'] == 'Gross Total']['due2author'].iloc[0]
            content.append(f"**Gross Total:** ${gross_total:.2f}")

        return "\n".join(content)

    def _save_to_file(self, markdown_content, per_author_page=False):
        if per_author_page:
            for author, author_content in zip(self.dataframe['Author Name'].unique(), markdown_content.split("\\newpage")):
                file_name = os.path.join("output", f"{author.replace(' ', '_').replace(',', '_').replace('\'', '_')}.md")
                file_name = file_name.replace('..', '.')
                file_name = file_name.replace('__', '_')
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(author_content)
        else:
            with open("LSI_author_reports.md", "w", encoding="utf-8") as f:
                f.write(markdown_content)

    def _save_to_pdf(self, markdown_content, per_author_page=False):
        extra_args=['-V', 'geometry:left=1in,right=0.75in,top=1in,bottom=1in']
        if per_author_page:
            for author, author_content in zip(self.dataframe['Author Name'].unique(), markdown_content.split("\\newpage")):
                file_name = os.path.join("output", f"KDP_{author.replace(' ', '_').replace(',', '_').replace('\'', '_')}.pdf")
                file_name = file_name.replace('..', '.')
                file_name = file_name.replace('__', '_')

                try:
                    pypandoc.convert_text(author_content, "pdf", "markdown", outputfile=file_name, extra_args=extra_args)
                    st.success(f"Successfully created PDF for {author}")
                except RuntimeError as e:
                    st.error(f"Error creating PDF for {author}: {e}")
        else:
            try:
                pypandoc.convert_text(markdown_content, "pdf", "markdown", outputfile="LSI_author_reports.pdf", extra_args=extra_args)
                st.success("Successfully created PDF report")
            except RuntimeError as e:
                st.error(f"Error creating PDF: {e}")