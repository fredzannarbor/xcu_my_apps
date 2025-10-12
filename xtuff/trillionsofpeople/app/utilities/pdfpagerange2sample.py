# -*- coding: utf-8 -*-
# script to extract a range of pages from a pdf file

import os

from PyPDF2 import PdfFileWriter, PdfFileReader

# Note: index starts at 1 and is inclusive of the end.
# The following will extract page 3 of the pdf file.
pdfs = {'BMC PP template.pdf': ({'start': 3, 'end': 3},)}


def get_pages(filename, startpage, endpage, savepath):
    startpage = int(startpage)
    endpage = int(endpage)
    pdf_reader = PdfFileReader(open(filename, 'rb'))
    pdf_writer = PdfFileWriter()
    print(f'Extracting pages {startpage} to {endpage} from {filename}')
    basefile = os.path.basename(filename)
    print('basefile: ', basefile)
    if basefile.startswith('978'):
        print('basefile starts with 978')
        output_filename = f'{basefile[0:12]}_sample_pages_{startpage}_to_{endpage}.pdf'
        print(f'Output filename: {output_filename[0:12]}_sample_pages_{startpage}_to_{endpage}.pdf')
    else:
        max = len(basefile)
        print(max)
        output_filename = f'{basefile[0:max]}_sample_pages_{startpage}_to_{endpage}.pdf'

    while startpage<=endpage:
        pdf_writer.addPage(pdf_reader.getPage(startpage-1))
        startpage+=1
    if not os.path.exists(savepath):
        os.makedirs(savepath)
    
    target_file = os.path.join(savepath, output_filename)
    
    print(f'Saving to {target_file}')
    with open(target_file,'wb') as out:
        pdf_writer.write(out)
    
    return target_file

if __name__ == "__main__":
    filename, startpage, endpage, savepath = '/Users/fred/unity/assets/interior_pdf/9781608882465_Sybil_v13_allisbns.pdf', 13, 30, '/Users/fred/unity/scratch'
    try:
        get_pages(filename, startpage, endpage, savepath)
    except Exception as e:
        print(e)
