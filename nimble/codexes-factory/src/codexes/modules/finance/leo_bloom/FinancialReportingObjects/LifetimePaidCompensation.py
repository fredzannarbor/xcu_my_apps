
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import load_spreadsheet
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects


class LifetimePaidCompensation(FinancialReportingObjects):
    def __init__(self, parent_instance, file_path=None):
        # Set paths first
        super().__init__(parent_instance)

        self.FRO_df_autosave_dir_path = parent_instance.FRO_df_autosave_dir_path
        self.FRO_object_autosave_dir_path = parent_instance.FRO_object_autosave_dir_path

        # Then handle the data
        if file_path is None:
            file_path = parent_instance.LSI_LTD_paid_file_path
        self.LSI_LTD_paid_file_path = file_path
        self.data = load_spreadsheet(self.LSI_LTD_paid_file_path)
        self.LSI_LTD_paid_df = self.data.astype({
            "ISBN": str,
            "Title": str,
            "Author": str,
            "Format": str,
            "Gross Qty": int,
            "Returned Qty": int,
            "Net Qty": int,
            "Net Compensation": float,
            "Sales Market": str
        })

        if self.is_LTD_paid_df_valid_shape(self.LSI_LTD_paid_df):
            self.dataframe = self.LSI_LTD_paid_df
        else:
            raise Exception("dataframe creation error")

    def is_LTD_paid_df_valid_shape(self, LSI_LTD_paid_df):
        number_columns = len(LSI_LTD_paid_df.columns)
        number_rows = len(LSI_LTD_paid_df.index)
        if number_columns != 9 or number_rows < 629:
            raise ValueError("Invalid shape of lifetime paid compensation object.")
        return True
