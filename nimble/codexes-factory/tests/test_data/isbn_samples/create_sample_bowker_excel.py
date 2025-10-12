#!/usr/bin/env python3
"""
Script to create a sample Bowker Excel file for testing the ISBN importer.
This creates a more complex Excel file with formatting, multiple sheets,
and additional metadata that might be present in real Bowker exports.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Ensure the output directory exists
os.makedirs('tests/test_data/isbn_samples', exist_ok=True)

# Create a DataFrame with sample data
def create_sample_data(num_records=20):
    # ISBN prefix for Nimble Books
    prefix = '978160888'
    
    # Generate sequential ISBNs
    isbns = [f"{prefix}{str(1000 + i).zfill(4)}" for i in range(num_records)]
    
    # Sample data
    formats = ['Paperback', 'Hardcover', 'E-book', 'Audio']
    statuses = ['Available', 'Privately Assigned', 'Publicly Assigned']
    imprints = ['Xynapse Traces', 'Nimble Books LLC', 'JP Cross']
    subjects = ['Artificial Intelligence', 'Computing', 'Business', 'Finance', 'Urban Planning']
    bisac_subjects = ['COM004000', 'COM043000', 'COM044000', 'BUS027000', 'SOC026030']
    series_names = ['AI Ethics Series', 'Quantum Series', 'ML Series', 'Data Science Series', '']
    
    # Generate random dates
    today = datetime.now()
    pub_dates = [(today + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d') if random.random() > 0.7 else None for _ in range(num_records)]
    assign_dates = [(today - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d') if pub_dates[i] is not None else None for i in range(num_records)]
    
    # Create the DataFrame
    df = pd.DataFrame({
        'ISBN': isbns,
        'Title': [f"Sample Book {i+1}" for i in range(num_records)],
        'Format': [random.choice(formats) for _ in range(num_records)],
        'Status': [random.choice(statuses) for _ in range(num_records)],
        'Publisher': ['Nimble Books LLC'] * num_records,
        'Imprint': [random.choice(imprints) for _ in range(num_records)],
        'Publication Date': pub_dates,
        'Assignment Date': assign_dates,
        'Author': ['AI Lab for Book-Lovers'] * num_records,
        'Price': [round(random.uniform(19.99, 39.99), 2) for _ in range(num_records)],
        'Currency': ['USD'] * num_records,
        'Language': ['eng'] * num_records,
        'Subject': [random.choice(subjects) for _ in range(num_records)],
        'BISAC Subject': [random.choice(bisac_subjects) for _ in range(num_records)],
        'Series Name': [random.choice(series_names) for _ in range(num_records)],
        'Series Number': [random.randint(1, 5) if random.random() > 0.5 else None for _ in range(num_records)],
        'Edition': ['First Edition'] * num_records,
        'Edition Number': [1] * num_records,
        'Pages': [random.randint(200, 500) for _ in range(num_records)],
        'Binding': ['Perfect Bound'] * num_records,
        'Trim Size': ['6 x 9'] * num_records,
        'Weight': [round(random.uniform(0.5, 1.5), 4) for _ in range(num_records)],
        'Carton Quantity': [24] * num_records,
        'Territory Rights': ['World'] * num_records,
        'Print Run': [random.randint(500, 2000) if random.random() > 0.7 else None for _ in range(num_records)],
        'Marketing Budget': [round(random.uniform(500, 5000), 2) if random.random() > 0.8 else None for _ in range(num_records)],
        'Notes': [f"Sample note for book {i+1}" if random.random() > 0.7 else None for i in range(num_records)]
    })
    
    # Update status based on dates
    for i, row in df.iterrows():
        if row['Publication Date'] is not None:
            df.at[i, 'Status'] = 'Publicly Assigned'
        elif row['Assignment Date'] is not None:
            df.at[i, 'Status'] = 'Privately Assigned'
        else:
            df.at[i, 'Status'] = 'Available'
    
    return df

# Create a summary sheet
def create_summary_data(main_df):
    status_counts = main_df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    format_counts = main_df['Format'].value_counts().reset_index()
    format_counts.columns = ['Format', 'Count']
    
    imprint_counts = main_df['Imprint'].value_counts().reset_index()
    imprint_counts.columns = ['Imprint', 'Count']
    
    return {
        'status': status_counts,
        'format': format_counts,
        'imprint': imprint_counts
    }

# Create metadata sheet
def create_metadata():
    return pd.DataFrame({
        'Property': ['Export Date', 'Account Number', 'Account Name', 'Total ISBNs', 'Export Version'],
        'Value': [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '12345', 'Nimble Books LLC', '1000', '2.3']
    })

# Main function to create the Excel file
def create_excel_file():
    # Create the main data
    main_data = create_sample_data(30)
    
    # Create summary data
    summary_data = create_summary_data(main_data)
    
    # Create metadata
    metadata = create_metadata()
    
    # Create Excel writer
    output_path = 'tests/test_data/isbn_samples/sample_bowker_complex.xlsx'
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Write main data
        main_data.to_excel(writer, sheet_name='ISBN Data', index=False)
        
        # Write summary data
        summary_data['status'].to_excel(writer, sheet_name='Summary', startrow=0, startcol=0, index=False)
        summary_data['format'].to_excel(writer, sheet_name='Summary', startrow=0, startcol=3, index=False)
        summary_data['imprint'].to_excel(writer, sheet_name='Summary', startrow=0, startcol=6, index=False)
        
        # Write metadata
        metadata.to_excel(writer, sheet_name='Metadata', index=False)
    
    print(f"Created sample Bowker Excel file at {output_path}")
    return output_path

if __name__ == "__main__":
    create_excel_file()