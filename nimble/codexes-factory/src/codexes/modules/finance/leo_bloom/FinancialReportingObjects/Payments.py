# Python
# Purpose: This file contains the class that handles payment tracking for leo_bloom_core
import pandas as pd
import streamlit as st
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.extend([parent_dir, grandparent_dir])

from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects




class Payments(FinancialReportingObjects):

    def __init__(self, parent_instance):
        super().__init__()
        self.parent_instance = parent_instance

    def ingest_hand_recorded_payments_from_csv(self):
        # add inbound payments2authors record to payments_df
        new_rows = pd.read_csv(self.actual_payment_history_file_path)
        st.write(self.actual_payment_history_file_path)
        try:
            hand_recorded_payments_df = self.dataframe
            hand_recorded_payments_df = pd.concat([hand_recorded_payments_df, new_rows])
           # # hand_recorded_payments_df.to_csv(userdocs_path
           #                     + '/results/'
           #                     + filename
           #                     + '.csv')
            hand_recorded_payments_df.to_csv("output/hand_recorded_payments.csv")
            return hand_recorded_payments_df
        except Exception as e:
            st.error(e)

    def ingest_payments_from_Paypal_csv(self, paypal_filename):
        paypal_df = pd.read_csv(paypal_filename)
        # march names in rows to royaltied author dict

        return paypal_df

    def ingest_payments_from_Stripe_csv(self, stripe_filename):
        stripedf = pd.read_csv(stripe_filename)
        # match mname in ingest data to nanme in royaltied df
        return stripedf

    def ingest_payments_from_Wise_csv(self, wise_filename):
        wisedf = pd.read_csv(wise_filename)
        # match mname in ingest data to nanme in royaltied df
        return wisedf

    def ingest_payments_from_Stripe_API(self, stripeinfo):
        return stripeAPIdf

    def get_payments(self):
        return self.payments_df

    def get_payments_by_date(self, date):
        return self.payments_df[self.payments_df['Date'] == date]

    def get_payments_by_date_range(self, start_date, end_date):
        return self.payments_df[(self.payments_df['Date'] >= start_date) & (self.payments_df['Date'] <= end_date)]

    def make_payments(self, payments_df):
        makepaydf = payments_df[
            'royaltied_author_id', 'payment_method', 'payment_address', 'due2author', 'payment_currency_code']
        # read list of payments2authors & coordinates
        if makepaydf['payment_method'] == 'PayPal':
            # PayPal API fx
            pass
        return
# we begin with manual ingest of payments2authors info contained in spreadsheets
