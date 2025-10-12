import streamlit as st
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects, AllUnitSalesThruToday

# Import other FRO classes
try:
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FullMetadataIngest import FullMetadataIngest
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.Add2FME import Add2FME
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.LSI_LTD_Paid_And_Unpaid_Compensation import LSI_LTD_Paid_And_Unpaid_Compensation
except ImportError:
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.FullMetadataIngest import FullMetadataIngest
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.Add2FME import Add2FME
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.LSI_LTD_Paid_And_Unpaid_Compensation import LSI_LTD_Paid_And_Unpaid_Compensation



class FullMetadataEnhanced(FinancialReportingObjects):
    INVALID_SHAPE_ERROR = "Invalid shape of Full Metadata Export dataframe."
    NO_ROWS_ERROR = "FME has no rows"

    def __init__(self, parent_instance, fme_file_path=None, add2fme_file_path=None):
        super().__init__()
        self.full_metadata_export = FullMetadataIngest(parent_instance, fme_file_path)
        self.add2fme = Add2FME(parent_instance, add2fme_file_path)
        self.lsi_ltd_paid_df = LSI_LTD_Paid_And_Unpaid_Compensation(parent_instance).dataframe
        self.dataframe = self.merge_data_frames()


    def merge_data_frames(self):
        try:
            # Ensure ISBN types are consistent (assume string for ISBN to preserve leading zeros)
            fme_df = self.full_metadata_export.dataframe_with_buy_links
            add2fme_df = self.add2fme.dataframe
            lsi_ltd_paid_df = self.lsi_ltd_paid_df

            fme_df['ISBN'] = fme_df['ISBN'].astype(str).str.strip()
            add2fme_df['ISBN'] = add2fme_df['ISBN'].astype(str).str.strip()
            lsi_ltd_paid_df['ISBN'] = lsi_ltd_paid_df['ISBN'].astype(str).str.strip()

            enhanced_df = fme_df.merge(add2fme_df[['ISBN', 'royaltied']], on='ISBN', how='left')
            enhanced_df = enhanced_df.merge(
                lsi_ltd_paid_df[['ISBN', 'Gross Qty', 'Returned Qty', 'Net Qty', 'Net Compensation']], on='ISBN',
                how='left')
            enhanced_df['royaltied'] = enhanced_df['royaltied'].fillna(False).astype('bool')
            enhanced_df["LTD Net Qty"] = enhanced_df["Net Qty"]
            return enhanced_df

        except Exception as e:
            st.error(f"Error in merging dataframes: {e}")
            raise



