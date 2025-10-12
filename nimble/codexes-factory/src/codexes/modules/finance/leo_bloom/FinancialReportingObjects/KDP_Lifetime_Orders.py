import logging
import os
import sys
import traceback

import streamlit as st
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.extend([parent_dir, grandparent_dir])

from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import load_spreadsheet
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects

class KDP_Lifetime_Orders(FinancialReportingObjects):
    def __init__(self, parent_instance, kdp_lifetime_orders_file_path=None):

        super().__init__(parent_instance.root)
        if kdp_lifetime_orders_file_path is None:
            kdp_lifetime_orders_file_path = parent_instance.kdp_lifetime_orders_file_path
            try:
                self.dataframe = load_spreadsheet(kdp_lifetime_orders_file_path)
                kdpdata = self.dataframe
            except Exception as e:
                st.error("Could not load kdp lifetime orders file.")
                st.error(f"{e}")
                logging.error(f"Could not load kdp lifetime orders file: {e}")
                st.write(traceback.print_exc())

        #return kdpdata

    def get_foreign_exchange_rates(self, kdpdata):
        st.info('getting foreign exchange rates')
        filename = f"ecb_{date.today():%Y%m%d}.zip"
        logging.info(filename)
        if not os.path.isfile(filename):
            logging.info('retrieving', ECB_URL)
            urllib.request.urlretrieve(ECB_URL, filename)
        else:
            logging.info('file already exists')
        c = CurrencyConverter(filename, fallback_on_wrong_date=True, fallback_on_missing_rate=True)
        st.info(f"Currency Converter loaded {filename}")

        #  ingest_kdp initially supports only post-2015 format KDP data

        # for each row, get the year from Royalty Date by doing a split
        # then get the month from Royalty Date by doing a split
        kdpdata['year'] = kdpdata['Royalty Date'].apply(lambda x: x.split('-')[0])
        kdpdata['month'] = kdpdata['Royalty Date'].apply(lambda x: x.split('-')[1])

        kdpdata['year'] = kdpdata['Royalty Date'].str.split('-').str[0]
        kdpdata['month'] = kdpdata['Royalty Date'].str.split('-').str[1]

        # long_month_name = kdpdate.split()[0]
        # year_name = kdpdate.split()[1]
        # month_number = datetime.datetime.strptime(long_month_name, "%B").month
        # year_number = datetime.datetime.strptime(year_name, "%Y").year
        # st.write(kdpdata['month'])

        first_date, last_date = c.bounds['USD']
        first_date, last_date = c.bounds['GBP']

        # get last day of month for year_number, month_number
        thisyear = int(kdpdata['year'].iloc[0])
        month_number = int(kdpdata['month'].iloc[0])
        last_day_of_this_month = last_day_of_month(date(thisyear, month_number, 1))


        kdpdata['exchangedate']: object = kdpdata['Royalty Date'].apply(lambda x: datetime.strptime(x, '%Y-%M'))
        # st.write(kdpdata['Currency'])
        # add column to kdpdata that calculates the last day of the month of "Royalty Date

        kdpdata['lookuproyaltyratedate'] = kdpdata['Royalty Date'].apply(
            lambda x: last_day_of_month(datetime.datetime.strptime(x, '%Y-%M')))
        # calculate conversion to usd for each currency/lookuproyaltyratedate pair
        kdpdata['exchangerate_on_lookupdate'] = kdpdata.apply(
            lambda x: c.convert(1, x['Currency'], 'USD', x['lookuproyaltyratedate']), axis=1)
        # create column USDeq_Royalty for each exchangerate_on_lookupdate * Royalty
        kdpdata['USDeq_Royalty'] = kdpdata.apply(lambda x: x['exchangerate_on_lookupdate'] * x['Royalty'], axis=1)
        # calculate Net Units Sold
        kdpdata['Net_Units_Sold'] = kdpdata.apply(lambda x: x['Units Sold'] - x['Units Refunded'], axis=1)
        return kdpdata
