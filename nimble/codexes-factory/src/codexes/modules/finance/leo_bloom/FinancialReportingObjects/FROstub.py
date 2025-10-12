
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import load_spreadsheet
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects, AllUnitSalesThruToday

class AppleDigitalAgencySales(FinancialReportingObjects):

    def __init__(self, parent_instance):
        # Set paths first
        super().__init__(parent_instance)
        self.apple_digital_agency_file_path = parent_instance.apple_digital_agency_file_path
        self.data = load_spreadsheet(self.apple_digital_agency_file_path)
        self.apple_digital_agency_df = self.data.astype({})
        self.dataframe = self.apple_digital_agency_df

        self.FRO_df_autosave_dir_path = parent_instance.FRO_df_autosave_dir_path
        self.FRO_object_autosave_dir_path = parent_instance.FRO_object_autosave_dir_path

