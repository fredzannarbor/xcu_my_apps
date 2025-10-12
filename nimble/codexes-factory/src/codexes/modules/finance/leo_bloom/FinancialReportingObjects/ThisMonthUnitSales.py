
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import load_spreadsheet
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects, AllUnitSalesThruToday


class ThisMonthUnitSales(FinancialReportingObjects):
    def __init__(self, parent_instance, file_path=None):
        super().__init__()
        if file_path is None:
            file_path = parent_instance.ThisMonthUnitSales_file_path
            self.data = load_spreadsheet(file_path)
        else:
            self.data = load_spreadsheet(file_path)
        self.columns = ["Title", "Author", "Format", "ISBN", "Units Sold"]
        self.dataframe = self.data.astype(
            {"ISBN": str, "Title": str, "Author": str, "Format": str, "Units Sold": int})
        # rename Units Sold to This Month Units Sold
        self.dataframe["This Month Units Sold"] = self.dataframe["Units Sold"].astype(int)
