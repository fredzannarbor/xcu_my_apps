from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects, AllUnitSalesThruToday

class LSI_Years_Data(FinancialReportingObjects):

    def __init__(self, parent_instance, years=[2022, 2023], file_path=None):
        super().__init__()
        self.years_dict = dict(zip(years, years))
        self.LSI_years_requested = years

    def add_default_years(self, years_dict=None, root=''):
        if years_dict is None:
            years_dict = {
                "2022": f"{root}/resources/data_tables/LSI/2022LSIcomp.xlsx",
                "2023": f"{root}/resources/data_tables/LSI/2023LSIComp.xlsx"
            }
        self.LSI_years_dict.update(years_dict)

    def add_to_dictionary(self, key, value):
        self.LSI_years_dict[key] = value
