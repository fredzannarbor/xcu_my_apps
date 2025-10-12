import logging
import traceback
import streamlit as st
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FRO_utilities import  load_spreadsheet
from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects

class Actual_Payment_History(FinancialReportingObjects):

    def __init__(self, parent_instance, actual_payment_history_file_path=None):
        if actual_payment_history_file_path is None:
            actual_payment_history_file_path = parent_instance.actual_payment_history_file_path
            try:
                self.dataframe = load_spreadsheet(actual_payment_history_file_path)
            except Exception as e:
                st.error("Could not load actual payment history file.")
                st.error(f"{e}")
                logging.error(f"Could not load actual payment history file: {e}")
                st.write(traceback.print_exc())
