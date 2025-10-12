
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import load_spreadsheet
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects, AllUnitSalesThruToday



class EstimatedUnpaidCompensation(FinancialReportingObjects):
    def __init__(self, parent_instance, file_path=None):
        super().__init__()
        if file_path is None:
            file_path = parent_instance.LSI_unpaid_file_path
        self.LSI_unpaid_file_path = file_path
        self.data = load_spreadsheet(self.LSI_unpaid_file_path)
        self.LSI_unpaid_df = self.data.astype(
            {"ISBN": str, "Title": str, "Author": str, "Format": str, "Gross Qty": int, "Returned Qty": int,
             "Net Qty": int, "Net Compensation": float, "Sales Market": str})
        self.is_LSI_unpaid_df_valid_shape(self.LSI_unpaid_df)
        if self.is_LSI_unpaid_df_valid_shape(self.LSI_unpaid_df):
            self.dataframe = self.LSI_unpaid_df
        else:
            raise Exception("dataframe creation error")

    def is_LSI_unpaid_df_valid_shape(self, LSI_unpaid_df):
        return LSI_unpaid_df.shape[1] == 9


