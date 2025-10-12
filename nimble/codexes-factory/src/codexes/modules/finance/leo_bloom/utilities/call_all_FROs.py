#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import logging
import os
import sys
import traceback

from classes_utilities import configure_logger

# print("Codexes2Gemini location:", Codexes2Gemini.__file__)

current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)

# Get the directory above the parent
grandparent_dir = os.path.dirname(parent_dir)

# Append both directories to the Python path
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

import src.classes.FinancialReportingObjects.FinancialReportingObjects as FROs

import streamlit as st



def run_streamlit_app():




    FRO = FROs.FinancialReportingObjects()
   # report_classes = [FROs.LSI_Royalties_Due, FROs.LifetimePaidCompensation, FROs.LSI_Year_Data, FROs.EstimatedUnpaidCompensation, FROs.KDP_Lifetime_Orders, FROs.ThisMonthUnitSales, FROs.AllUnitSalesThruToday, FROs.FullMetadataEnhanced, FROs.FullMetadataIngest, FROs.Add2FME]
    report_classes = [FROs.LSI_Royalties_Year_Calculations,FROs.LifetimePaidCompensation, FROs.EstimatedUnpaidCompensation, FROs.ThisMonthUnitSales, FROs.FullMetadataEnhanced, FROs.FullMetadataIngest, FROs.Add2FME,  FROs.KDP_Lifetime_Orders ]

    dataframe_sections = {}  # Dictionary to store section names and positions

    for i, report_class in enumerate(report_classes):
        try:
            report_instance = report_class(FRO)
        except Exception as e:
            logging.error(traceback.format_exc())
            st.error(traceback.format_exc())
            continue

        if hasattr(report_instance, 'dataframe'):
            dataframe_sections[report_class.__name__] = i  # Store section position
            # check if key is found in dataframe
            # if "Combined Sales" in report_instance.dataframe.columns:
            #    # show Combined Sales sheet only
            #     st.write(report_instance.dataframe["sheetname"] == "Combined Sales")
            # #t.dataframe(report_instance)

    # Create navigation sidebar
    selected_section = st.sidebar.selectbox("Go to DataFrame:", list(dataframe_sections.keys()))

    # Display the selected DataFrame
    for report_class, section_index in dataframe_sections.items():
        if selected_section == report_class:
            report_instance = report_classes[section_index](FRO)  # Recreate instance
            st.write(f"DataFrame for {report_class}:")
            st.dataframe(report_instance.dataframe)
            break  # Only display the selected section



def main(port=1967, themebase="light"):
    sys.argv = ["streamlit", "run", __file__, f"--server.port={port}", f'--theme.base={themebase}',
                f'--server.maxUploadSize=40']
    import streamlit.web.cli as stcli
    stcli.main()
    configure_logger("DEBUG")

if __name__ == "__main__":
    run_streamlit_app()