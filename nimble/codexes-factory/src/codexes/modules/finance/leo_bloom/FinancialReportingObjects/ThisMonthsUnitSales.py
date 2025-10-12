
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import load_spreadsheet
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects


class ThisMonthUnitSales(FinancialReportingObjects):
    def __init__(self, parent_instance, file_path=None):
        super().__init__()
        if file_path is None:
            file_path = parent_instance.this_month_unit_sales_file_path
        self.data = load_spreadsheet(file_path)
        self.dataframe = self.data.astype(
            {"ISBN": str, "Title": str, "Author": str, "Format": str, "Units Sold": int})
        self.dataframe = self.dataframe.sort_values(by='Units Sold', ascending=False, na_position='last')
        self.dataframe = self.dataframe.reset_index(drop=True)
        self.dataframe["This Month Units Sold"] = self.dataframe["Units Sold"].astype(int)
        self.dataframe["This Month Units Sold"] = self.dataframe["This Month Units Sold"].fillna(0)

