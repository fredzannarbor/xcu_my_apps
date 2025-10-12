import streamlit as st
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.extend([parent_dir, grandparent_dir])

from src.classes.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects

from src.classes.utilities.classes_utilities import configure_logger
from src.classes.FinancialReportingObjects.Authors import Authors
from src.classes.FinancialReportingObjects.CombinedAuthorReports import GenerateCombinedAuthorReports
from src.classes.FinancialReportingObjects.LSI_Year_Data import LSI_Year_Data
from src.classes.FinancialReportingObjects.KDP_Lifetime_Orders import KDP_Lifetime_Orders
from src.classes.FinancialReportingObjects.RightsRevenueAuthorReports import RightsRevenues

# Initialize logger
configure_logger("INFO")


class AuthorReportSetup(GenerateCombinedAuthorReports): #inherit
    """
    Represents a setup for generating combined author reports by inheriting from
    `GenerateCombinedAuthorReports`. Handles data preparation and report generation for
    various revenue sources.

    Provides a framework for loading and preparing data from different sources like LSI,
    KDP, and rights reports. The class supports generating combined author revenue
    reports, including the ability to handle author name resolution via source-of-truth
    mapping files.

    Attributes:
        root (str): Root directory path for accessing file paths and resources.
        lsi_report_path (str): File path to the interim LSI reports CSV.
        kdp_report_path (str): File path to the KDP report CSV.
        rights_report_path (str): File path to the rights revenues interim CSV.
        resolve_author_names_file_path (str): Path to the author names resolution JSON
            source-of-truth file.
        year (int): Default year for which reports are prepared.
        lsi_df (pandas.DataFrame or None): DataFrame containing processed LSI data,
            initialized as None.
        kdp_df (pandas.DataFrame or None): DataFrame containing processed KDP data,
            initialized as None.
        rights_df (pandas.DataFrame or None): DataFrame containing processed rights
            data, initialized as None.
    """
    def __init__(self, root): # Added root param
        self.root = root # Add root param
        super().__init__(self)

        self.resolve_author_names_file_path = f'{self.root}/resources/sources_of_truth/authornames2authorcodes.json'
        self.year = 2024 # default
        LSI_year_data_instance = LSI_Year_Data(self)
        KDP_Lifetime_Orders_instance = KDP_Lifetime_Orders(self)
        rights_revenue_instance = RightsRevenues(self)
        self.lsi_df = LSI_year_data_instance.dataframe
        self.kdp_df = KDP_Lifetime_Orders_instance.dataframe
        self.rights_df = rights_revenue_instance.dataframe
        # st.write(self.kdp_df)
        # st.write(self.lsi_df)
        # st.write(self.rights_df)

        self.authors = Authors(
                self, self.resolve_author_names_file_path, self.kdp_df, self.lsi_df, self.rights_df
            )
        self.kdp_df = self.process_kdp_data()
        self.rights_df = self.modify_rights_data()


    def process_kdp_data(self):
            self.kdp_df["Row_Type"] = "Detail"  # Default to "Detail"
            self.subtotal_rows = (self.kdp_df["Title"].str.contains("Subtotal", na=False) | self.kdp_df["Title"].str.contains("Total",
                                                                                                               na=False))
            # Calculate 'due2author' here:
            self.kdp_df['Royalty'] = self.kdp_df['Royalty'].astype(float)  # Ensure Royalty is a numeric type
            self.kdp_df['author_share'] = 0.3  # Set author share – make this configurable if needed
            self.kdp_df["due2author"] = self.kdp_df['Royalty'] * self.kdp_df['author_share']

            return self.kdp_df  # Return the modified kdp_df

    def modify_rights_data(self):

            self.rights_df["Author Share"] = self.rights_df["Author Share"].astype(
                float
            )  # Ensure Author Share is float
            self.rights_df["Due to Author"] = (
                self.rights_df["Net Compensation"] *self.rights_df["Author Share"]
            )  # Assuming 'Net Compensation' is already numeric.
            return self.rights_df  # Return modified rights_df


if __name__ == '__main__':
        # Setup Streamlit app
        st.title("Author Combined Sales Report Generator")

        year = st.sidebar.selectbox("Select Year", [2024])
        output_format = st.sidebar.selectbox("Output Format", ["streamlit", "markdown", "pdf"], index=2)
        per_author_page = st.sidebar.checkbox("Separate PDF Pages Per Author", value=True)
        FROs = FinancialReportingObjects()
        # Create an instance of the class
        combined_report = AuthorReportSetup(root=grandparent_dir) # Provide root path
        st.write(combined_report.kdp_df, combined_report.lsi_df, combined_report.rights_df)

        with st.spinner("Generating reports..."):
            combined_report.run(output_format=output_format, year=year, per_author_page=per_author_page)

