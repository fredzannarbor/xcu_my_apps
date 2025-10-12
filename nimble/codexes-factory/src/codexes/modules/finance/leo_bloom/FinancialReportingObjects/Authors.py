import pandas as pd
import streamlit as st
import json

from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects


class Authors(FinancialReportingObjects):
    def __init__(
        self,
        parent_instance,
        raw_names_source,
        author_codes_source,
        kdp_df=None,
        lsi_df=None,
        rights_df=None,  # Add rights_df
    ):
        super().__init__(parent_instance.root)

        self.author_codes_data = self.load_author_codes(author_codes_source)  # Load author codes

        self.raw_author_names = self.extract_raw_names(raw_names_source, lsi_df, kdp_df, rights_df)
        self.resolved_author_names, self.author_codes_dict = self.resolve_author_names(self.raw_author_names, self.author_codes_data)

        if kdp_df is not None:
            self.map_author_codes_to_dataframe(kdp_df, "Author Name")
        if lsi_df is not None:
            self.map_author_codes_to_dataframe(lsi_df, "Contributor 1 Name")
        if rights_df is not None:  # Map for rights_df
            self.map_author_codes_to_dataframe(rights_df, "Author Name")

    def load_author_codes(self, source):
        try:
            with open(source, 'r') as f:
                data = json.load(f)
            return data.get("authors", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            st.error(f"Error loading author codes: {e}")
            return []

    def extract_raw_names(self, lsi_df, kdp_df, rights_df):
        for source in [lsi_df, kdp_df, rights_df]:
            if isinstance(source, pd.DataFrame):
                if lsi_df is not None:
                    return lsi_df["Contributor 1 Name"].unique().tolist()
                elif kdp_df is not None:
                    return kdp_df["Author Name"].unique().tolist()
                elif rights_df is not None:
                    return rights_df["Author Name"].unique().tolist()
            elif isinstance(source, list):
                return source

        return []

    def resolve_author_names(self, raw_names, author_codes_data):
        resolved_names = {}
        author_codes_dict = {} # create dictionary for fast lookups
        for author_data in author_codes_data:
            code = author_data['author code']
            resolved_name = author_data['Resolved name']
            resolved_names[code] = resolved_name
            author_codes_dict[code] = author_data.get("LSI names", []) + author_data.get("KDP names", [])
        return resolved_names, author_codes_dict


    def map_author_codes_to_dataframe(self, df, name_column):
        def get_author_code(name):
            for code, names in self.author_codes_dict.items():
                if name in names:
                    return code
            return None

        df["Author Code"] = df[name_column].apply(get_author_code)

    def __repr__(self):
        return (f"Author Mapping:\n"
                f"  Raw Names: {len(self.raw_author_names)}\n"
                f"  Resolved Names: {len(self.resolved_author_names)}\n")