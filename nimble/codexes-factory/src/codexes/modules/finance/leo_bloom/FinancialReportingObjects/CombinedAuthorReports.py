import json
import logging
import traceback

import pandas as pd
import streamlit as st

import os
import pypandoc

from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import (
    FinancialReportingObjects
)

from codexes.modules.finance.leo_bloom.utilities.classes_utilities import ensure_directory_exists
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.Payments import Payments


class AuthorNames2AuthorCodes(FinancialReportingObjects):

    def __init__(self, parent_instance):
        super().__init__()
        self.resolve_author_names_df = None
        file_path = parent_instance.resolve_author_names_file_path

        self.resolve_author_names_file_path = file_path
        st.write(self.resolve_author_names_file_path)
        self.authornames2authorcodes_dict = {}
        self.authornames2authorcodes_df = self.read_in_resolve_author_names_file()
        self.year = 2024


    def read_in_resolve_author_names_file(self):
        try:
            import json
            file_path = os.path.expanduser(self.resolve_author_names_file_path)  # Expand ~
            with open(file_path, 'r') as f:
                author_data = json.load(f)
            self.authornames2authorcodes_dict = author_data
            authors = author_data.get("authors", [])  # Handle potential missing "authors" key
            self.resolve_author_names_df = pd.DataFrame(authors)  # Create the DataFrame here

            return self.resolve_author_names_df, self.authornames2authorcodes_dict  # Return the DataFrame

        except (FileNotFoundError, json.JSONDecodeError) as e:
            st.error(f"Error loading or parsing author names JSON file: {e}")
            return None


class GenerateCombinedAuthorReports(FinancialReportingObjects):

    def __init__(self, parent_instance):
        super().__init__(parent_instance.root)
        self.year = 2024
        self.parent_instance = parent_instance
        with open(self.parent_instance.resolve_author_names_file_path, 'r') as f:
            self.authornames2authorcodes_dict = json.load(f)
        self.boilerplate = """
LSI is Lightning Source, Inc., a subsidiary of Ingram, the largest US book distributor. Ingram has distribution partners in most of the world's largest book markets.

KDP is Kindle Direct Publishing, a service of Amazon.com, which also has  distribution partners and online stores in major book markets.

Sales and revenue reported are those for which payment was _received_ during the calendar year. 

The amount due to author is calculated as a percentage of gross revenue excluding any income tax withheld by foreign authorities. (This is normally only the case with rights sales.)

Negative values represent items returned from the bookseller as unsold or unsatisfactory.

Going forward all payments2authors must be via PayPal, Stripe, or check. Bank transfers are no longer supported.
"""

    def generate_combined_author_reports(
            self,
            lsi_reports_df,
            kdp_reports_df,
            rights_revenues_df,
            output_format="PDF",
            per_author_page=True,
    ):

        st.write(lsi_reports_df)
        # Save interim data for debugging or further analysis
        lsi_reports_df.to_csv("output/lsi_reports_interim.csv", index=False)
        kdp_reports_df.to_csv("output/kdp_reports_interim.csv", index=False)
        rights_revenues_df.to_csv("output/rights_revenues_interim.csv", index=False)
        print("Saved dataframes to CSV.")
        st.write('---')
        st.write(lsi_reports_df)
        all_author_names = set()

        for df, col in [(lsi_reports_df, "Contributor 1 Name"), (kdp_reports_df, "Author Name"),
                        (rights_revenues_df, "Author Name")]:
            if df is not None and not df.empty:
                try:  # Handle missing columns gracefully
                    all_author_names.update(df[col].astype(str).unique()) # add unique to the set
                except KeyError:
                    logging.warning(f"Column '{col}' not found in a dataframe")
                    continue
        all_author_names = sorted(list(all_author_names))  # if you need a sorted list after
        # get length of list of all_author_names
        len_list = len(all_author_names)
        st.write(f"length of all_author_names: {len_list}")
        #st.write(f"all author names: {all_author_names}")
        all_author_codes = []
        authors_data = self.authornames2authorcodes_dict.get("authors", [])  # Access the "authors" list

        for author in authors_data: # list of items
            for author_name in all_author_names:
                if author_name in author.get("KDP names", []) or author_name in author.get("LSI names", []):
                    all_author_codes.append(author["author code"])
                    break
        st.write(f"length of all_author_codes: {len(all_author_codes)}" )
        st.write(f"all author codes {all_author_codes}")
        report_content = []
        payments_due_data = []
        # sort author codes list

        st.spinner("Generating reports...")
        author_reports_generated = 0
        for author_code in all_author_codes:
            author_content = []
            total_due_to_author = 0

            # get resolved author name for this author code
            for author_info in authors_data:
                if author_code == author_info["author code"]:
                    resolved_name = author_info["Resolved name"]
                    break

            author_content.append(
                f"### {resolved_name}\n\n"
                f"##### Combined Sales Report 2024"
            )

            sales_data = []
            for reports_df, name_column in [
                (lsi_reports_df, "Contributor 1 Name"),
                (kdp_reports_df, "Author Name"),
                (rights_revenues_df, "Author Name"),
            ]:
                if reports_df is not None and not reports_df.empty:
                    report_author_df = reports_df[
                        reports_df["Author Code"] == author_code
                        ]
                    if not report_author_df.empty:
                        if reports_df is kdp_reports_df:  # KDP Report

                            for title, title_group in report_author_df.groupby("Title"):
                                if title not in ["Author Subtotal", "Gross Total"]:
                                    subtotal_due2author = title_group[
                                        title_group["Row_Type"] == "Detail"
                                        ]["due2author"].sum()
                                    total_units = title_group[
                                        title_group["Row_Type"] == "Detail"
                                        ]["Net Units Sold"].sum()
                                    sales_data.append({
                                        "Channel": "KDP",
                                        "Title": title,
                                        "Net Units": total_units,
                                        "Net Compensation": title_group["USDeq_Royalty"].round(2).sum(),
                                        "Author Share": "30%",# title_group["author_share"].unique(),
                                        "Due to Author": subtotal_due2author.round(2)
                                    })
                                    total_due_to_author += subtotal_due2author

                        elif reports_df is lsi_reports_df:  # LSI Report

                            for title, title_group in report_author_df.groupby("Title"):

                                if title not in ['Author Subtotal', 'Gross Total']:
                                    total_units = title_group[
                                        title_group["Row_Type"] == "Detail"
                                        ]["Net Qty"].sum()
                                    total_due2author = title_group[
                                        title_group["Row_Type"] == "Detail"
                                        ]["due2author"].sum()
                                    title_group["Net Compensation"] = title_group["Net_Comp_Recd_2024"]
                                    total_net_compensation = title_group[title_group["Row_Type"] == "Detail"]["Net Compensation"].sum().round(2)
                                    #st.write(title, total_net_compensation)
                                    sales_data.append({
                                        "Channel": "LSI",
                                        "Title": title,
                                        "Net Units": total_units,
                                        "Net Compensation": total_net_compensation,
                                        "Author Share": "30%",# title_group["author_share"].unique(),
                                        "Due to Author": total_due2author.round(2)
                                    })
                                    total_due_to_author += total_due2author

                        elif reports_df is rights_revenues_df:  # Rights Revenue Report

                            for title, title_group in report_author_df.groupby("Title"):
                                total_due2author = title_group["Due to Author"].round(2).sum()
                                sales_data.append({
                                    "Channel": "Rights Revenue",
                                    "Title": title,
                                    "Net Compensation": total_due2author,
                                    "Author Share": "50%", #title_group["Author Share"].unique(),

                                    "Net Units": "N/A",  # Assuming no units for rights revenue
                                    "Due to Author": total_due2author.round(2)
                                })
                                total_due_to_author += total_due2author

            # Convert sales_data into a DataFrame and display as a table
            if sales_data:
                sales_df = pd.DataFrame(sales_data)
                st.write(sales_df)
              #  st.table(sales_df)  # Use st.table for static tables or st.dataframe for interactive tables

                # If you want to keep the table in the markdown report, you could also do:
                author_content.append(sales_df.to_markdown(index=False))



            author_content.append(
                f"##### **Total Due to Author**: ${total_due_to_author:.2f}\n\n"
            )
            author_content.append("* * *")
            # try:
            #     actual_payments = Actual_Payment_History(FinancialReportingObjects)
            #     st.write(actual_payments)
            # except Exception as e:
            #     logging.error("could not load actual payment history")
            #     st.error(e)
            #     st.error(traceback.format_exc())

            if output_format == "pdf":

                author_content.append(f"""{self.boilerplate}""")  # Add two newlines here

                if per_author_page:
                    report_content.append("\n".join(author_content + ["\n\\newpage\n"]))
                    with open(os.path.join("output", f"{author_code}.md"), "w", encoding="utf-8") as f:
                        f.write("\n".join(author_content + ["\n\\newpage\n"]))
                else:
                    report_content.extend(author_content + ["---"])
                report_markdown = "\n\n".join(author_content)
                print(report_markdown)
                st.info(f"saving report for author code {author_code} /  {resolved_name} to PDF")
                self._save_to_pdf(report_markdown, author_code, resolved_name, per_author_page=True)
                author_reports_generated += 1


            # Collect data for payments2authors due
            payments_due_data.append({
                "Author Code": author_code,
                "Author Name": resolved_name,
                "Total Due": total_due_to_author,
            })
        st.success(f"{author_reports_generated} author reports generated")
        st.write("---")
        full_report = "\n".join(report_content)
        FROs = FinancialReportingObjects()
        st.write(f"Payments History")
        payments_object = Payments(FROs)
        hand_recorded_payments = payments_object.ingest_hand_recorded_payments_from_csv()
        st.write(hand_recorded_payments)

        if output_format == "streamlit":
            st.markdown(full_report, unsafe_allow_html=True)
        #elif output_format == "pdf":

        elif output_format == "markdown":
            self._save_to_file(full_report, per_author_page)

        # Save the payments2authors due data to a DataFrame
        self._save_payments_due_to_dataframe(payments_due_data)

    def _save_payments_due_to_dataframe(self, payments_due_data):
        """Saves payment due information into a DataFrame and then to a CSV file.

        Args:
            payments_due_data (list): List of dictionaries with author payment information.
        """
        try:
            payments_df = pd.DataFrame(payments_due_data)
            payments_df.to_csv("output/payments_due.csv", index=False)
        except Exception as e:
            import traceback
            print(traceback.format_exc())

    def _save_to_pdf(self, markdown_content, author_code, author_name, per_author_page=True):
        extra_args = ["-V", "geometry:left=1in,right=0.75in,top=1in,bottom=1in"]
        if per_author_page:

                author_filename = author_name.replace(' ', '_').replace(',', '_').replace("'", '_')
                file_name = os.path.join(
                    "output",
                    f"{author_filename}_{author_code}_{self.year}.pdf")
                file_name.replace("..", ".")
                file_name = file_name.replace("__", "_")

                try:
                    pypandoc.convert_text(
                        markdown_content,
                        "pdf",
                        "markdown",
                        outputfile=file_name,
                        extra_args=extra_args,
                    )
                    st.success(f"Successfully created PDF combined sales report for {author_name}")
                except RuntimeError as e:
                    st.error(f"Error creating PDF for {author_name}: {e}")
                    st.error(traceback.format_exc())
        else:
            try:
                pypandoc.convert_text(
                    markdown_content,
                    "pdf",
                    "markdown",
                    outputfile="output/combined_author_reports.pdf",
                    extra_args=extra_args,
                )
                st.success(f"Successfully created PDF report at output/combined_author_reports.pdf")
            except RuntimeError as e:
                st.error(f"Error creating PDF: {e}")

    def _save_to_file(self, markdown_content, per_author_page=False):
        ensure_directory_exists("output")
        if per_author_page:
            for author_content in markdown_content.split("\\newpage"):
                with open(os.path.join("output", f"combined_author_report.md"), "w", encoding="utf-8") as f:
                    f.write(author_content)
            st.success("Successfully created combined author report markdown file.")
        else:
            with open(os.path.join("output", f"combined_author_report.md"), "w", encoding="utf-8") as f:
                f.write(markdown_content)
            st.success("Successfully created combined author report markdown file.")
