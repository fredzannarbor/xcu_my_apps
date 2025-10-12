from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects, AllUnitSalesThruToday


class LSI_Royalties_Due(FinancialReportingObjects):

    def __init__(self, parent_instance, file_path=None, calculation_basis="pay_on_receipt"):
        super().__init__()
        if file_path is None:
            file_path = parent_instance.lsi_royalties_due_file_path
        self.lsi_royalties_due_file_path = file_path
        self.calculation_basis = calculation_basis
        self.dataframe = self.create_LSI_royalties_df(parent_instance)
        self.is_LSI_royalty_df_valid()
