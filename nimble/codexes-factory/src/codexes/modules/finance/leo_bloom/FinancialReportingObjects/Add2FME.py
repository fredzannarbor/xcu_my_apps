
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import load_spreadsheet
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects, AllUnitSalesThruToday



class Add2FME(FinancialReportingObjects):
    '''
    Proprietary or analytic data from Nimble Books to add to the FME by matching on ISBN
    '''

    def __init__(self, parent_instance, file_path=None):
        super().__init__(parent_instance.root)
        self.file_path = file_path or parent_instance.add2fme_file_path
        self.dataframe = load_spreadsheet(self.file_path)
        self.clean_up_Add2FME()

    def clean_up_Add2FME(self):
        self.dataframe['ISBN'] = self.dataframe['ISBN'].astype(str)
        # remove commas from ISBN
        self.dataframe['ISBN'] = self.dataframe['ISBN'].str.replace(',', '')
