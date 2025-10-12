import streamlit as st
import pandas as pd
import os
import logging
import pypandoc

from codexes.modules.finance.leo_bloom.FinancialReportingObjects import FinancialReportingObjects, LSI_Royalties_Year_Calculations


class LSIAuthorReports(FinancialReportingObjects):

    def __init__(self, parent_instance, year): # Add year argument
        super().__init__(parent_instance.root)
        self.parent_instance = parent_instance
        self.year = year # Store year
        self.royalties_calcs = LSI_Royalties_Year_Calculations(self.parent_instance, years=[self.year])  # Correct instantiation
        self.dataframe = pd.DataFrame() # Start with empty dataframe
        self.dataframe = self.generate_author_report_df() # call with parent

    def generate_author_report_df(self, authors=None, output_format="streamlit"):
        df = self.royalties_calcs.dataframe.copy()
        df['due2author'] = df['due2author'].round(2)  # Round all due2author to 2 decimal places

        print(df.shape)
        logging.info(df['Contributor 1 Name'].unique().tolist())  # Changed to list for clarity

        if authors is None or 'all' in (authors if isinstance(authors, list) else [authors]):
            filtered_df = df
        else:
            authors = [authors] if not isinstance(authors, list) else authors
            mask = df['Contributor 1 Name'].str.contains('|'.join(authors), case=False, na=False)
            filtered_df = df[mask]

        logging.info(f"Shape of filtered_df: {filtered_df.shape}")

        report_data = []
        net_comp_col = f"Net_Comp_Recd_{self.year}"
        st.write(f"net_comp_col is {net_comp_col}")
        for author_name, author_group in filtered_df.groupby('Contributor 1 Name'):
            author_total = 0
            author_group['Row_Type'] = 'Detail'

            report_data.append((author_name, []))
            for title, title_group in author_group.groupby('Title'):
                for title, title_group in author_group.groupby('Title'):
                    st.write(f"title group is {title_group}")
                    title_details = title_group[title_group['Row_Type'] == 'Detail'].copy()
                    title_subtotal = title_details['due2author'].sum()

                title_details['Net Qty'] = title_group['Net Qty']
                if net_comp_col in title_group:
                    compensation_values = title_group[net_comp_col]
                    title_details['Net Compensation'] = compensation_values.round(2)
                    title_details[net_comp_col] = compensation_values  # Keep both columns in sync
                else:
                    print(f"Warning: {net_comp_col} not found in data for title {title}")
                    title_details['Net Compensation'] = 0.0
                    title_details[net_comp_col] = 0.0

                # Add debugging
                print(f"Title: {title}")
                print(f"Compensation column values: {title_group[net_comp_col].value_counts()}")
                print(f"Number of zero compensation rows: {(title_details['Net Compensation'] == 0).sum()}")

                # Subtotal row
                title_subtotal_row = pd.DataFrame([{
                    "Title": title, "ISBN": "", "Sales Market": "", "Net Qty": "",
                    "Net Compensation": "", "author_share": "", "due2author": title_subtotal,
                    "Contributor 1 Name": author_name, "Row_Type": "Subtotal"
                }])

                report_data[-1][1].extend(title_details.to_dict('records'))
                report_data[-1][1].extend(title_subtotal_row.to_dict('records'))
                author_total += title_subtotal

            # Author total row
            author_total_row = pd.DataFrame([{
                "Title": "Author Subtotal", "ISBN": "", "Sales Market": "", "Net Qty": "",
                "Net Compensation": "", "author_share": "", "due2author": author_total,
                "Contributor 1 Name": author_name, "Row_Type": "Author Subtotal"
            }])

            report_data[-1][1].extend(author_total_row.to_dict('records'))

        gross_total = filtered_df['due2author'].sum().round(2)
        gross_total_row = pd.DataFrame([{
            "Title": "Gross Total", "ISBN": "", "Sales Market": "", "Net Qty": "",
            "Net Compensation": "", "author_share": "", "due2author": gross_total,
            "Contributor 1 Name": "", "Row_Type": "Gross Total"
        }])

        flat_report_data = [item for author, rows in report_data for item in rows]
        flat_report_data.extend(gross_total_row.to_dict('records'))

        return pd.DataFrame(flat_report_data)

    def lsi_author_report_df2format(self, output_format="pdf", authors=None, per_author_page=True):
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
        st.write(markdown_content)

        if output_format == "streamlit":
            st.markdown(markdown_content, unsafe_allow_html=True)
        elif output_format == "pdf":
            self._save_to_pdf(markdown_content, per_author_page)
        elif output_format == "markdown":
            self._save_to_file(markdown_content, per_author_page)

    def _generate_markdown_content(self, authors='all', per_author_page=False):
        content = []
        filtered_df = self.dataframe if authors is None or 'all' in (authors if isinstance(authors, list) else [authors]) else self.dataframe[self.dataframe['Contributor 1 Name'].isin(authors)]
        print(filtered_df)
        st.write("filtered df")
        # drop the row where title == "Gross Total"
        filtered_df = filtered_df[filtered_df['Title'] != "Gross Total"]
        for author, author_group in filtered_df.groupby('Contributor 1 Name'):

            author_content = [f"### {author}"]

            for title, group in author_group.groupby('Title'):
                if title not in ["Author Subtotal", "Gross Total"]:
                    # creates title row
                    # get the format for the title
                    title_format = group[group['Row_Type'] == 'Detail']['Format'].iloc[0]
                    author_content.append(f"#### {title} - {title_format}")
                    details = group[group['Row_Type'] == 'Detail'].round(2)
                    # creates tab;e
                    table_md = "\n| ISBN        | Sales Market | Net Qty | Net Compensation | Author Share | Due to Author |\n" \
                               "|-------------|--------------|---------|-------------------|--------------|---------------|\n"

                    for _, row in details.iterrows():
                        isbn_padded = row['ISBN'].ljust(14)  # Pad ISBN to 14 characters
                        table_md += f"| {isbn_padded} | {row['Sales Market']} | {row['Net Qty']} | {row[f'Net_Comp_Recd_{self.year}']:.2f} | {row['author_share']:.2f} | ${row['due2author']:.2f} |\n"

                    author_content.append(table_md)

                    if not group[group['Row_Type'] == 'Subtotal'].empty:
                        title_subtotal = group[group['Row_Type'] == 'Subtotal']['due2author'].iloc[0]
                        author_content.append(f"**Subtotal:** ${title_subtotal:.2f}\n")

            if not author_group[author_group['Row_Type'] == 'Author Subtotal'].empty:
                author_subtotal = author_group[author_group['Row_Type'] == 'Author Subtotal']['due2author'].iloc[0]
                author_content.append(f"**AUTHOR GRAND TOTAL:** ${author_subtotal:.2f}\n")


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
            for author, author_content in zip(self.dataframe['Contributor 1 Name'].unique(), markdown_content.split("\\newpage")):
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
            for author, author_content in zip(self.dataframe['Contributor 1 Name'].unique(), markdown_content.split("\\newpage")):
                file_name = os.path.join("output", f"{author.replace(' ', '_').replace(',', '_').replace('\'', '_')}.pdf")
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