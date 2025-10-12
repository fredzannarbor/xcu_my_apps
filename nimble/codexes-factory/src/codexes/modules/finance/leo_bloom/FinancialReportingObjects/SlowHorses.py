from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import AllUnitSalesThruToday, FinancialReportingObjects


class SlowHorses(FinancialReportingObjects):
    # must add all unit sales
    def __init__(self, parent_instance):
        # lifetime net qty <=5
        self.dataframe = AllUnitSalesThruToday(parent_instance).dataframe
        # slow horses are titles with less than 10 lifetime sales
        self.slow_horses = self.dataframe[(self.dataframe['Net New Qty'] <= 5) & (self.df['Net New Qty'] > 0)]
        self.glue_factory = self.dataframe[self.dataframe['Net New Qty'] == 0]
