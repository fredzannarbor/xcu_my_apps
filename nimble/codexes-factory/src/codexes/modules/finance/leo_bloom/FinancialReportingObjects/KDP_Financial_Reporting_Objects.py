import pandas as pd
import streamlit as st
import numpy as np
import glob
import urllib
import os
import datetime
from datetime import date
import urllib.request
from currency_converter import CurrencyConverter
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import last_day_of_month

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip"

class Kindle_Financial_Reporting_Objects(FinancialReportingObjects):

    def __init__(self, root="~/bin/nimble/LeoBloom_uv", file_path=None):
    # initialize FRO with default file values
    # they can be overridden when creating specific objects
        self.root = root
        self.file_path=file_path
        self.kdp_lifetime_orders_file_path = f"{root}/resources/data_tables/KDP/lifetime_orders.xlsx"


class Ingest_KDP_by_Month(Kindle_Financial_Reporting_Objects):

    def __init__(self, parent_instance):
        super().__init__(parent_instance.root)
        self.parent_instance = parent_instance
        self.dataframe = pd.DataFrame()


    def ingest_kdp_by_month(userdocs_kdpdata_path):
        FYI = st.empty()
        FYI.info('getting foreign exchange rates')
        filename = f"ecb_{date.today():%Y%m%d}.zip"
        print(filename)
        if not os.path.isfile(filename):
            print('retrieving', ECB_URL)
            urllib.request.urlretrieve(ECB_URL, filename)
        else:
            print('file already exists')
        c = CurrencyConverter(filename, fallback_on_wrong_date=True, fallback_on_missing_rate=True)
        print('loaded', filename)

        #  ingest_kdp initially supports only post-2015 format KDP data
        dkdp = pd.DataFrame()
        kdpdatatarget = userdocs_kdpdata_path + '/' + 'K*.xlsx'
        print('just before i loop')
        for i in glob.glob(kdpdatatarget):
            imessage = "ingesting KDP data file " + str(i)
            FYI.info(imessage)

            getdate = pd.read_excel(i, header=0, sheet_name='Total Royalty')
            # print(getdate)
            kdpdate = getdate.columns[1]
            # get month & date from file
            kdpdata = pd.read_excel(i, header=1, sheet_name='Total Royalty')

            kdpdata['month'] = kdpdate.split()[0]
            kdpdata['year'] = kdpdate.split()[1]
            long_month_name = kdpdate.split()[0]
            year_name = kdpdate.split()[1]
            month_number = datetime.datetime.strptime(long_month_name, "%B").month
            year_number = datetime.datetime.strptime(year_name, "%Y").year

            # get last day of month for year_number, month_number
            last_day_of_this_month = last_day_of_month(datetime.date(year_number, month_number, 1))

            first_date, last_date = c.bounds['USD']
            print('first_date', first_date, 'last_date', last_date)
            first_date, last_date = c.bounds['GBP']
            print('GBP first_date', first_date, 'last_date', last_date)
            exchangedate = datetime.datetime(year_number, month_number, last_day_of_this_month.day)
            kdpdata.insert(0, "Report Date", exchangedate)
            lookupdate = exchangedate.strftime('%F')

            print(lookupdate)
            cusd = 1.0
            # Currency conversions with error handling and fallback rates
            currency_rates = {}
            fallback_rates = {
                'USD': 1.0, 'GBP': 1.25, 'EUR': 1.10, 'JPY': 0.0067,
                'AUD': 0.65, 'CAD': 0.74, 'BRL': 0.18, 'MXN': 0.05, 'INR': 0.012
            }

            for currency in ['GBP', 'EUR', 'JPY', 'AUD', 'CAD', 'BRL', 'MXN', 'INR']:
                try:
                    currency_rates[currency] = c.convert(1, currency, 'USD', date=exchangedate)
                except Exception as e:
                    st.warning(f'Error converting {currency} to USD, using fallback rate: {e}')
                    currency_rates[currency] = fallback_rates[currency]

            # Extract individual rates for backward compatibility
            cgbp = currency_rates['GBP']
            ceur = currency_rates['EUR']
            cjpy = currency_rates['JPY']
            caud = currency_rates['AUD']
            ccad = currency_rates['CAD']
            cbrl = currency_rates['BRL']
            cmxn = currency_rates['MXN']
            cinr = currency_rates['INR']

            conditions = [
                kdpdata['Currency'] == 'USD',
                kdpdata['Currency'] == 'GBP',
                kdpdata['Currency'] == 'EUR',
                kdpdata['Currency'] == 'JPY',
                kdpdata['Currency'] == 'AUD',
                kdpdata['Currency'] == 'CAD',
                kdpdata['Currency'] == 'BRL',
                kdpdata['Currency'] == 'MXN',
                kdpdata['Currency'] == 'INR']

            choices = [
                kdpdata['Royalty'] * cusd,
                kdpdata['Royalty'] * cgbp,
                kdpdata['Royalty'] * ceur,
                kdpdata['Royalty'] * cjpy,
                kdpdata['Royalty'] * caud,
                kdpdata['Royalty'] * ccad,
                kdpdata['Royalty'] * cbrl,
                kdpdata['Royalty'] * cmxn,
                kdpdata['Royalty'] * cinr
            ]

            kdpdata['USDeq_Royalty'] = np.select(conditions, choices, default=0)
            kdpdata['USDeq_Royalty'] = kdpdata['USDeq_Royalty'].round(2)

            kdpdata['Net Units Sold'] = kdpdata['Units Sold'] - kdpdata['Units Refunded']
            print(kdpdata['Net Units Sold'])

            dkdp = dkdp.append(kdpdata, ignore_index=True)

        dkdp.to_csv(userdocs_kdpdata_path + '/dkdp.csv')
        return dkdp

class Ingest_KDP_Lifetime_Data(Kindle_Financial_Reporting_Objects):

    def __init__(self, parent_instance):
        super().__init__(parent_instance.root)
        self.parent_instance = parent_instance
        self.dataframe = pd.DataFrame()



    def _get_kdp_sheet_name(self, file_path: str) -> str:
        """Determine the correct sheet name for different KDP file types."""
        import os
        try:
            file_name = os.path.basename(file_path)
            print(f"🔍 DEBUG: KDP Lifetime analyzing file name pattern: {file_name}")

            # For KDP_Order* or KDP_Orders- files, use "Combined Sales" sheet
            if file_name.startswith('KDP_Order'):
                print(f"🔍 DEBUG: KDP Lifetime - KDP_Order*/KDP_Orders- pattern detected -> 'Combined Sales' sheet")
                return 'Combined Sales'

            # For other KDP file patterns, try to detect available sheets
            excel_file = pd.ExcelFile(file_path)
            available_sheets = excel_file.sheet_names
            print(f"🔍 DEBUG: KDP Lifetime - Available sheets: {available_sheets}")

            # Priority order for sheet names
            preferred_sheets = ['Combined Sales', 'Total Royalty', 'Royalty', 'Sales']

            for preferred in preferred_sheets:
                if preferred in available_sheets:
                    print(f"🔍 DEBUG: KDP Lifetime - Found preferred sheet '{preferred}'")
                    return preferred

            # If no preferred sheet found, use the first available sheet
            if available_sheets:
                print(f"🔍 DEBUG: KDP Lifetime - Using first available sheet: '{available_sheets[0]}'")
                return available_sheets[0]

            # Fallback to 'Combined Sales'
            print(f"🔍 DEBUG: KDP Lifetime - No sheets detected, fallback to 'Combined Sales'")
            return 'Combined Sales'

        except Exception as e:
            # Default fallback
            print(f"🔍 DEBUG: KDP Lifetime - Error in sheet detection: {e}, fallback to 'Combined Sales'")
            return 'Combined Sales'

    def ingest_kdp_lifetime_data(self, filepath):
        import os
        file_name = os.path.basename(filepath)

        # Determine correct sheet name based on file type
        sheet_name = self._get_kdp_sheet_name(filepath)

        # Debug output showing which sheet is being read
        print(f"🔍 DEBUG: Reading sheet '{sheet_name}' from KDP Lifetime file {file_name}")
        st.info(f"Reading sheet '{sheet_name}' from file {file_name}")

        kdpdata = pd.read_excel(filepath, sheet_name)
        print(f"shape on load is {kdpdata.shape}")
        cols_on_load = kdpdata.columns
        print(f"data on load is {kdpdata.head()}")
        FYI = st.empty()
        FYI.info('getting foreign exchange rates')
        filename = f"ecb_{date.today():%Y%m%d}.zip"
        print(filename)
        if not os.path.isfile(filename):
            print('retrieving', ECB_URL)
            urllib.request.urlretrieve(ECB_URL, filename)
        else:
            print('file already exists')
        c = CurrencyConverter(filename, fallback_on_wrong_date=True, fallback_on_missing_rate=True)
        print('loaded', filename)

        #  ingest_kdp initially supports only post-2015 format KDP data

        # for each row, get the year from Royalty Date by doing a split
        # then get the month from Royalty Date by doing a split
        kdpdata['year'] = kdpdata['Royalty Date'].apply(lambda x: x.split('-')[0])
        kdpdata['month'] = kdpdata['Royalty Date'].apply(lambda x: x.split('-')[1])


        thisyear = int(kdpdata['year'].iloc[0])
        month_number = int(kdpdata['month'].iloc[0])
        last_day_of_royalty_incurring_month = last_day_of_month(datetime.date(thisyear, month_number, 1))
        first_date, last_date = c.bounds['USD']
        first_date, last_date = c.bounds['GBP']
        kdpdata['exchangedate']: object = kdpdata['Royalty Date'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m'))

        # add column to kdpdata that calculates the first day of the month of "Royalty Date"
        kdpdata['lookuproyaltyratedate'] = kdpdata['Royalty Date'].apply(
            lambda x: datetime.datetime.strptime(x, '%Y-%m').replace(day=1).date())
        # calculate conversion to usd for each currency/lookuproyaltyratedate pair with error handling
        def safe_currency_convert(row):
            try:
                return c.convert(1, row['Currency'], 'USD', row['lookuproyaltyratedate'])
            except Exception as e:
                # Fallback rates if conversion fails
                fallback_rates = {
                    'USD': 1.0, 'GBP': 1.25, 'EUR': 1.10, 'JPY': 0.0067,
                    'AUD': 0.65, 'CAD': 0.74, 'BRL': 0.18, 'MXN': 0.05, 'INR': 0.012
                }
                st.warning(f'Error converting {row["Currency"]} to USD for date {row["lookuproyaltyratedate"]}, using fallback rate: {e}')
                return fallback_rates.get(row['Currency'], 1.0)

        kdpdata['exchangerate_on_lookupdate'] = kdpdata.apply(safe_currency_convert, axis=1)
        # create column USDeq_Royalty for each exchangerate_on_lookupdate * Royalty
        kdpdata['USDeq_Royalty'] = kdpdata.apply(lambda x: x['exchangerate_on_lookupdate'] * x['Royalty'], axis=1)
        # calculate Net Units Sold
        kdpdata['Net Units Sold'] = kdpdata.apply(lambda x: x['Units Sold'] - x['Units Refunded'], axis=1)
        cols_final = kdpdata.columns
        new_columns = [col for col in cols_final if col not in cols_on_load]
        print(f"New columns added: {new_columns}")

        dropped_or_renamed_columns = [col for col in cols_on_load if col not in cols_final]
        print(f"Columns dropped or possibly renamed: {dropped_or_renamed_columns}")
        self.dataframe = kdpdata
        return kdpdata

    def create_year_objects(self, years_requested=[2024]):
        years_data = {}
        for index, row in self.kdpdata.iterrows():
            year = int(row['year'])
            if year in years_requested:
                if year not in years_data:
                    years_data[year] = []
                years_data[year].append(row)

        for year, data in years_data.items():
            st.write(f"## KDP Data for {year}")
            st.dataframe(pd.DataFrame(data))
            st.write(pd.DataFrame(data).shape)
            # save to resources directory
            pd.DataFrame(data).to_csv(f"resources/data_tables/KDP/{year}_KDP_sales.csv")
        self.years_data = years_data
        return years_data