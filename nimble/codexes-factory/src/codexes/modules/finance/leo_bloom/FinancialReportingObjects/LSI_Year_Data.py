from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import load_spreadsheet
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects


class LSI_Year_Data(FinancialReportingObjects):

    def __init__(self, parent_instance, file_path=None):
        super().__init__()
        if file_path is None:
            file_path = parent_instance.LSI_year_data_file_path
        self.LSI_year_data_file_path = file_path
        self.dataframe = load_spreadsheet(self.LSI_year_data_file_path)
        self.dataframe = self.dataframe.astype(
            {"ISBN": str, "Title": str, "Author": str, "Format": str, "Gross Qty": int, "Returned Qty": int,
             "Net Qty": int, "Net Compensation": float, "Sales Market": str})
        # self.is_LSI_year_data_df_valid_shape(self.LSI_year_data_df)

