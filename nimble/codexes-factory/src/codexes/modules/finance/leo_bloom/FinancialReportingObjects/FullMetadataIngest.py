
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import add_amazon_buy_links, load_spreadsheet
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects, AllUnitSalesThruToday

class FullMetadataIngest(FinancialReportingObjects):
    def __init__(self, parent_instance, fme_file_path=None):
        super().__init__()
        self.fme_file_path = fme_file_path or parent_instance.fme_file_path
        self.dataframe = self.load_and_validate_data()


    def load_and_validate_data(self):
        try:
            df = load_spreadsheet(self.fme_file_path)
            st.info(f'LOADING DATA from {self.fme_file_path}')
            # Validate shape
            if df.shape[1] < 100:
                raise ValueError("Invalid shape of Full Metadata Export dataframe.")
            if df.shape[0] < 1:
                raise ValueError("FME has no rows")

            # Data transformations
            df['isbn_10_bak'] = df['ISBN'].apply(lambda x: to_isbn10(x) if len(str(x)) == 13 else x)
            df['Ean'] = df['Ean'].fillna(0).astype(int).astype(str).replace(',', '')
            df["Pub Date"] = pd.to_datetime(df["Pub Date"])

            # Add Amazon buy links
            fme_with_buy_links = add_amazon_buy_links(df)
            fme_with_buy_links.to_excel("resources/data_tables/LSI/Nimble_Books_Catalog.xlsx")
            return fme_with_buy_links

        except Exception as e:
            st.error(f"An error occurred while processing FME: {e}")
            raise

    @property
    def dataframe_with_buy_links(self):
        return self.dataframe
