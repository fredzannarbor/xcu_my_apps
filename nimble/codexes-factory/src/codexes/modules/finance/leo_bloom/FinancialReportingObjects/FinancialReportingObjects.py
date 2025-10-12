#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
"""
This class creates financial reporting objects to be shared by the leo_bloom_core library.
Priorities are:
- accuracy
- modularity
- reusability

Begin with the following objects:
Lifetime Paid Compensation Received from LSI
Estimated Unpaid Compensation Owed by LSI
Full Metadata Export from LSI

New objects:
 Merge Lifetime Paid and Estimatedd Unpaid Compensation Owed by LSI
 Merge Full Metadata Export with Merged Compensation on ISBN

"""
import logging
import os
import sys
from datetime import datetime  # Import the specific classes you need
import pickle

import pandas as pd
import streamlit as st

# Import following current patterns
try:
    from codexes.modules.finance.leo_bloom.utilities.classes_utilities import configure_logger
except ModuleNotFoundError:
    try:
        from src.codexes.modules.finance.leo_bloom.utilities.classes_utilities import configure_logger
    except ModuleNotFoundError:
        # Fallback for missing configure_logger
        def configure_logger(level):
            import logging
            logging.basicConfig(level=level)
            return logging.getLogger(__name__)

# Forward declarations to avoid circular imports
FullMetadataEnhanced = None

# Next: create all_unit_sales as UnitSalesThroughToday

class FinancialReportingObjects:

    def __init__(self, root="/Users/fred/initiatives/nimble/repos/codexes-leo-bloom"):
        self.root = root
        logging.info(f"root is {self.root}")
        self.FRO_df_autosave_dir_path = os.path.join(self.root, "autosave", "dataframes")

        self.FRO_object_autosave_dir_path = os.path.join(self.root, "autosave", "objects")

        # Ensure directories exist
        os.makedirs(self.FRO_df_autosave_dir_path, exist_ok=True)
        os.makedirs(self.FRO_object_autosave_dir_path, exist_ok=True)

        try:
            # TODO - create test data files



            self.LSI_LTD_paid_file_path = f"{root}/resources/data_tables/LSI/LSI_LTD_paid_comp.xlsx"
            self.LSI_unpaid_file_path = f"{root}/resources/data_tables/LSI/LSI_estimated_unpaid_comp.xlsx"
            self.this_month_unit_sales_file_path = f"{root}/resources/data_tables/LSI/ThisMonthUnitSales.xlsx"
            self.fme_file_path = f"{root}/resources/data_tables/LSI/Full_Metadata_Export.xlsx"
            self.LSI_year_data_file_path = f"{root}/resources/data_tables/LSI/2024LSIComp.xlsx"
            self.kdp_lifetime_orders_file_path = f"{root}/resources/data_tables/KDP/lifetime_orders.xlsx"

            # Maintain these myself.
            self.rights_revenue_file_path = f"{root}/resources/sources_of_truth/rights_revenue.csv"
            self.add2fme_file_path = f"{root}/resources/sources_of_truth/add2fme.xlsx"
            self.actual_payment_history_file_path = f"{root}/resources/sources_of_truth/payments2authors/hand_recorded_payments_to_authors.csv"
            self.resolve_author_names_file_path = (f"{root}/resources/sources_of_truth/authornames2authorcodes.json")
            self.direct_sales_file_path = f"{root}/resources/sources_of_truth/direct_sales.xlsx"
            self.ecommerce_sales_file_path = f"{root}/resources/sources_of_truth/ecommerce_sales.xlsx"
            self.apple_digital_agency_file_path = f"{root}/resources/sources_of_truth/apple_digital_agency.xlsx"
            # compute these
            logging.info(f"Created LTD, unpaid, combined, FME objects")

            self.lsi_royalties_due_file_path = f"{root}/resources/data_tables/LSI/LSI_royalties_due.csv"
            self._full_metadata_enhanced_df = None #

            self.dataframe = pd.DataFrame()
            # duplicate column "

        except Exception as e:
            logging.error(f"Could not create all the FROs")
            logging.error(f"{e}")
            st.error(f"{e}")

    @property
    def full_metadata_enhanced_df(self):
        if self._full_metadata_enhanced_df is None:  # Check if already loaded
            # Lazy import to avoid circular dependencies
            global FullMetadataEnhanced
            if FullMetadataEnhanced is None:
                try:
                    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FullMetadataEnhanced import FullMetadataEnhanced
                except ImportError:
                    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.FullMetadataEnhanced import FullMetadataEnhanced

            self._full_metadata_enhanced_df = FullMetadataEnhanced(self).dataframe  # Load only once
        return self._full_metadata_enhanced_df  # Return the stored DataFrame
    # for help debugging

    def identify_mixed_type_columns(df):
        mixed_type_columns = []
        for col in df.columns:
            num_of_data_types = len(df[col].apply(type).unique())
            if num_of_data_types > 1:
                mixed_type_columns.append(col)
                print(f"{col}: {df[col].apply(type).unique()}")
        return mixed_type_columns



    def autosave_dataframe(self):
        """
        Saves the most recent instantiation of the class.dataframe to a CSV file.
        """
        utc_now = datetime.utcnow()
        # filename = f"{self.__class__.__name__}_{utc_now.strftime('%Y%m%d_%H%M%S')}.csv"
        filename = f"{self.__class__.__name__}.csv"

        filepath = os.path.join(self.FRO_df_autosave_dir_path, filename)
        try:
            self.dataframe.to_csv(filepath, index=False)
            logging.info(f"DataFrame autosaved to {filepath}")
        except Exception as e:
            logging.error(f"Failed to autosave DataFrame: {e}")

    def autosave_object(self):
        """
        Saves the latest version of the class as an object to a file
        """
        utc_now = datetime.utcnow()
        #filename = f"{self.__class__.__name__}_{utc_now.strftime('%Y%m%d_%H%M%S')}.csv"
        filename = f"{self.__class__.__name__}_.pkl"
        filepath = os.path.join(self.FRO_object_autosave_dir_path, filename)
        try:
            with open(filepath, 'wb') as file:
                pickle.dump(self, file)
        except Exception as e:
            logging.error(f"Failed to autosave object: {e}")

    def __setattr__(self, name, value):
        """
        Overridden to trigger autosave methods when 'dataframe' attribute is altered.
        """
        super().__setattr__(name, value)
        if name == 'dataframe':
            self.autosave_dataframe()
            self.autosave_object()


def main(port=1455, themebase="light"):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}", f'--theme.base={themebase}',
                f'--server.maxUploadSize=40']
    import streamlit.web.cli as stcli
    stcli.main()
    configure_logger("INFO")


if __name__ == '__main__':
    FRO = FinancialReportingObjects()
    ltd = FRO.LifetimePaidCompensation(f"resources/data_tables/LSI/LSI_LTD_paid_comp.xlsx")
    est = FRO.EstimatedUnpaidCompensation("resources/data_tables/LSI/LSI_estimated_unpaid_comp.csv")
    payment_object = FRO.LTD_Paid_And_Unpaid_Compensation(ltd, est)
    df3 = payment_object.create_LSI_LTD_paid_and_unpaid_comp()
    print(df3)
    metadata_object = FRO.FullMetadataExport(
        f"resources/data_tables/LSI/Full_Metadata_Export.csv")
    fme = metadata_object.create_fme()
    print(fme)

