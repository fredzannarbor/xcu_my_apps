from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects, AllUnitSalesThruToday
import streamlit as st
import logging
import traceback
import pandas as pd

from codexes.modules.finance.leo_bloom.FinancialReportingObjects.LSI_Year_Data import LSI_Year_Data


class LSI_Royalties_Year_Calculations(FinancialReportingObjects):
    def __init__(self, parent_instance, years=[2024], file_path=None):
        super().__init__(parent_instance.root)

        self.years = years
        self.parent_instance = parent_instance # Add this
        self.dataframe = self.create_LSI_year_sales_df(parent_instance)

    def create_LSI_year_sales_df(self, parent_instance):
        try:
            fme_df = parent_instance.full_metadata_enhanced_df
            all_year_dfs = []

            for year in self.years:
                try:
                    lsi_year_data_df = LSI_Year_Data(
                        self.parent_instance,
                        file_path=f"{self.parent_instance.root}/resources/data_tables/LSI/{year}LSIComp.xlsx"
                    ).dataframe

                except FileNotFoundError as e:
                    logging.error(f"File for year {year} not found: {e}")
                    st.error(f"Data for year {year} is not available.")
                    continue

                except Exception as e:
                    logging.error(f"Error loading data for year {year}: {e}")
                    st.error(f"An error occurred loading data for {year}: {e}")
                    continue
                try:
                    # Remove duplicates from BOTH DataFrames before merging
                    lsi_year_data_df_deduplicated = lsi_year_data_df.drop_duplicates(subset=['ISBN', 'Sales Market'])

                    fme_royaltied = fme_df[fme_df['royaltied'] == True][['ISBN', 'Title', 'Contributor 1 Name', 'Format', 'Pub Date']]
                    fme_royaltied_deduplicated = fme_royaltied.drop_duplicates(subset=['ISBN']) # Deduplicate FME

                    merged_df = lsi_year_data_df_deduplicated.merge(
                        fme_royaltied_deduplicated,
                        on='ISBN',
                        how='inner'
                    )
                    # Add year-specific columns and calculate due2author
                    merged_df[f'Net_Comp_Recd_{year}'] = merged_df['Net Compensation']
                    merged_df['author_share'] = 0.3
                    merged_df['due2author'] = merged_df[f'Net_Comp_Recd_{year}'] * merged_df['author_share']
                    # show only two decimals for due2author
                    merged_df['due2author'] = merged_df['due2author'].round(2)


                    merged_df['Royalty Year'] = year
                    # make royalty year a string
                    merged_df['Royalty Year'] = merged_df['Royalty Year'].astype(str)

                    # change "Format_x" to "Format"
                    # change format_y to "Binding" and put it next to "Format"
                    merged_df.rename(columns={'Format_x': 'Format', 'Format_y': 'Binding'}, inplace=True)
                    merged_df.rename(columns={'Title_x': 'Title'}, inplace=True)
                    # drop column "Title_y"
                    merged_df.drop(columns=['Title_y'], inplace=True)
                    # drop Net Compensation
                    merged_df.drop(columns=['Net Compensation'], inplace=True)

                    all_year_dfs.append(merged_df)

                except KeyError as e:
                    logging.error(f"KeyError during merge for {year}: {e}")
                    st.error(f"Column mismatch during merge for {year}.")
                    st.write(traceback.format_exc())  # Show detailed traceback in Streamlit
                    continue

                except Exception as e:
                    logging.error(f"Error merging data for {year}: {e}")
                    st.error(f"An error occurred merging data for {year}: {e}")
                    st.write(traceback.format_exc())  # Show traceback
                    continue

            if all_year_dfs:
                combined_df = pd.concat(all_year_dfs, ignore_index=True)
                return combined_df
            else:
                logging.warning("No valid dataframes for any year.")
                st.warning("No valid data processed for any year.")
                return pd.DataFrame()

        except Exception as e:
            logging.error(f"Unexpected error in create_LSI_year_sales_df: {e}")
            st.error(f"An unexpected error occurred: {e}")
            st.write(traceback.format_exc())
            return pd.DataFrame()