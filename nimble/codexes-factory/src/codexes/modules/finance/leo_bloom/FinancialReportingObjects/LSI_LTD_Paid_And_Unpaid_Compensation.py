from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects, AllUnitSalesThruToday

class LSI_LTD_Paid_And_Unpaid_Compensation(FinancialReportingObjects):
    def __init__(self, parent_instance, LSI_LTD_paid_file_path=None, LSI_unpaid_file_path=None):
        super().__init__()
        self.ltd_paid_df = LifetimePaidCompensation(parent_instance, LSI_LTD_paid_file_path).dataframe
        self.unpaid_df = EstimatedUnpaidCompensation(parent_instance, LSI_unpaid_file_path).dataframe
        # get len paid rows
        self.len_paid_rows = len(self.ltd_paid_df)
        # concatenate the dfs
        self.LSI_paid_and_unpaid_df = pd.concat([self.ltd_paid_df, self.unpaid_df])
        self.LSI_pup_rows = len(self.LSI_paid_and_unpaid_df)
        self.LSI_pup_columns = len(self.LSI_paid_and_unpaid_df.columns)
        self.is_LSI_paid_and_unpaid_df_valid_shape(self.len_paid_rows, self.LSI_pup_rows, self.LSI_pup_columns)
        self.dataframe = self.LSI_paid_and_unpaid_df

    def is_LSI_paid_and_unpaid_df_valid_shape(self, paid_rows, pup_rows, pup_columns):
        if pup_columns != 9 or pup_rows < paid_rows:
            raise ValueError("Invalid shape of combined dataframesf")
        return True

    def set_dtypes_for_LSI_LTD_Paid_And_Unpaid(self):
        self.dataframe = self.groupby('ISBN').agg({
            'Title': 'first',
            'Author': 'first',
            'Format': 'first',
            'Gross Qty': 'sum',
            'Returned Qty': 'sum',
            'Net Qty': 'sum',
            'Net Compensation': 'sum',
            'Sales Market': 'first'
        }).reset_index()
        self.dataframe = self.dataframe.sort_values(by='Net Compensation', ascending=False, na_position='last')
        return self

