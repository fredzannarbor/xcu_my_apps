import argparse

import pandas as pd
import streamlit as st


def select_rendition():
    rendition = st.selectbox(
        "Select Rendition",
        ("POD"),
    )
    return rendition


def select_trim_size():
    trim_size = st.selectbox(
        "Select Trim Size",
        ("5.5 x 8.5", "6 x 9", "7.5 x 10", "8.5 x 11"),
    )
    return trim_size


def select_interior_color():
    interior_color = st.selectbox(
        "Select Interior Color",
        ("Black and White", "Black and White with Color Cover", "Color"),
    )
    return interior_color


def select_interior_paper():
    interior_paper = st.selectbox(
        "Select Interior Paper",
        ("60# Offset", "70# Offset", "80# Offset", "100# Offset", "80# Gloss Text", "100# Gloss Text"),
    )
    return interior_paper


def select_binding():
    binding = st.selectbox(
        "Select Binding",
        ("Perfect Bound", "Saddle Stitched"),
    )
    return binding


def select_cover_finish():
    cover_finish = st.selectbox(
        "Select Cover Finish",
        ("Gloss", "Matte"),
    )
    return cover_finish


def select_specs():
    rendition = select_rendition()
    trimsize = select_trim_size()
    interior_color = select_interior_color()
    interior_paper = select_interior_paper()
    binding = select_binding()
    cover_finish = select_cover_finish()
    specs_dict = dict(rendition=rendition, trimsize=trimsize, interior_color=interior_color,
                      interior_paper=interior_paper, binding=binding, cover_finish=cover_finish)
    return specs_dict


def assemble_lsi_specs_label(rendition, trimsize, interior_color, interior_paper, binding, cover_finish):
    booktype = f"{rendition}: {interior_color} {trimsize} {binding} on {interior_paper} w/  {cover_finish}"
    return booktype


def calculate_spinewidth(sheetname, finalpagecount):
    """Enhanced spine width calculation with improved error handling"""
    try:
        from .spine_width_calculator import SpineWidthCalculator
        
        # Use enhanced calculator
        calculator = SpineWidthCalculator()
        spine_width = calculator.calculate_spine_width_from_lookup(finalpagecount, sheetname)
        
        print(f'Calculated spine width: {spine_width} for {finalpagecount} pages, paper type: {sheetname}')
        return spine_width
        
    except Exception as e:
        print(f'Error in enhanced spine width calculation: {e}')
        # Fallback to original implementation
        return _calculate_spinewidth_original(sheetname, finalpagecount)


def _calculate_spinewidth_original(sheetname, finalpagecount):
    """Original spine width calculation as fallback"""
    try:
        print('entering calculate_spinewidth (original)')
        dict_of_sheets = pd.read_excel('resources/data_tables/LSI/SpineWidthLookup.xls', sheet_name=None)

        # get the sheet matching sheetname and make it a dataframe with column names "Pages" and "SpineWidth"
        df = dict_of_sheets[sheetname]
        df.columns = ["Pages", "SpineWidth"]
        df["Pages"] = df["Pages"].astype(int)
        df["SpineWidth"] = df["SpineWidth"].astype(float)
        finalpagecount = int(finalpagecount)
        
        if finalpagecount < df["Pages"].min():
            print("Warning: page count is less than the smallest page count for the paper group and binding type")
            return df["SpineWidth"].min()
        elif finalpagecount > df["Pages"].max():
            print("Warning: page count is greater than the largest page count for the paper group and binding type")
            return df["SpineWidth"].max()
        elif finalpagecount == df["Pages"].min():
            return df["SpineWidth"].min()
        elif finalpagecount == df["Pages"].max():
            return df["SpineWidth"].max()
        else:
            return df.loc[df["Pages"] >= finalpagecount, "SpineWidth"].min()
            
    except Exception as e:
        print(f'Error in original spine width calculation: {e}')
        return 0.25  # Safe fallback


def calculate_binding_type(finalpagecount, trimsize, color_interior, BISACs):
    if finalpagecount < 160:
        if color_interior:
            if BISACs.contains("History"):
                binding_type = "Case"
            else:
                binding_type = "Perfect"
        else:
            binding_type = "Perfect"
    else:  # page gt 160
        if color_interior:
            if not BISACs.contains("Naval"):
                binding_type = "Case"
            else:
                binding_type = "Perfect"
        else:
            binding_type = "Case"
    return binding_type


def calculate_sheetname(papercolor, color_interior, paperweight, binding, cover_finish):
    # papercolor = "White" always
    # interiorcolor from metadatas
    if paperweight == "50# Offset":
        paperweight = "50"
    if paperweight == "60# Offset":
        paperweight = "60"
    elif paperweight == "70# Offset":
        paperweight = "70"

    else:
        return "Error: invalid paperweight"
    if binding == "Perfect Bound":
        binding = "Perfect"
    elif binding == "Saddle Stitched":
        binding = "Saddle"
    elif binding == "Case":
        binding = "Case"
    else:
        return "Error: invalid binding"
    if cover_finish == "Gloss":
        cover_finish = "Glossy"
    elif cover_finish == "Matte":
        cover_finish = "Matte"
    else:
        return "Error: invalid cover finish"
    sheetname = f"{papercolor} {color_interior} {paperweight} {binding} {cover_finish}"
    return sheetname

def find_closest_trim_ratio(width, height, input_ratio):
    # calculate area of input trim size
    input_area = width * height # sqyare inches
    # read in trim sizes and ratios
    trim_sizes_df = pd.read_csv('resources/data_tables/LSI/trim_sizes_and_ratios.csv', index_col=0)
    trim_sizes_df['area'] = trim_sizes_df['height'] * trim_sizes_df['width']
    trim_ratios = trim_sizes_df['ratio']
    sorted_ratios = trim_ratios.sort_values()
    # find five closest ratios
    closest_ratios = sorted_ratios.iloc[(sorted_ratios - input_ratio).abs().argsort()[:5]]
    #print(closest_ratios)
    # calculate area of closest ratios
    closest_ratios_df = trim_sizes_df[trim_sizes_df['ratio'].isin(closest_ratios)]
    magnitudes_df = closest_ratios_df.copy()
    magnitudes_df['area_diff'] = abs(magnitudes_df['area'] - input_area)
    magnitudes_df = magnitudes_df.sort_values(by='area_diff')

    print(magnitudes_df)
    # return the row with the smallest area difference
    return magnitudes_df.iloc[0]






if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rendition", "-r", type=str, default="POD")
    parser.add_argument("--trimsize", "-t", type=str, default="5.5 x 8.5")
    parser.add_argument("--width", "-W", type=float, default=5.5)
    parser.add_argument("--height", "-H", type=float, default=8.5)
    parser.add_argument("--color_interior", "-c", type=str, default="Black and White")
    parser.add_argument("--papercolor", "-p", type=str, default="60# Offset")
    parser.add_argument("--paperweight", "-w", type=str, default="50")
    parser.add_argument("--binding", "-b", type=str, default="Perfect Bound")
    parser.add_argument("--cover_finish", "-M", type=str, default="Matte")
    parser.add_argument("--directly_specify_sheetname", "-d", type=str, default="Standard Color 50 Perfect")
    parser.add_argument("--finalpagecount", "-f", type=str, default="100")
    parser.add_argument("--trim-ratio", "-R", type=float, default=1.414)
    args = parser.parse_args()
    if args.directly_specify_sheetname:
        sheetname = args.directly_specify_sheetname
    else:
        sheetname = args.papercolor + " " + args.color_interior + " " + args.paperweight + " " + args.binding
    spinewidth = calculate_spinewidth(sheetname, args.finalpagecount)
    print('spinewidth is', spinewidth)
    recommended_trim_size = find_closest_trim_ratio(args.width, args.height, args.trim_ratio)
    print(recommended_trim_size)
