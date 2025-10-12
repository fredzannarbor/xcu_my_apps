import argparse
from pathlib import Path

import fitz


def resize_unevenly_sized_pages(pdf_file, output_file, width, height):
    """
    Resize unevenly sized pages to a specified width and height.
    """
    pdf_file = Path(pdf_file)
    output_file = Path(output_file)
    print(pdf_file, output_file, width, height)
    src = fitz.Document(pdf_file)
    doc = fitz.Document()
    for ipage in src:
        rotation = ipage.rotation
        if rotation in {90, 270}:
            fmt = fitz.paper_rect("letter-p")
            ipage.set_rotation(0)
        else:
            fmt = fitz.paper_rect("letter-p")
        print(fmt.width, fmt.height)
        page = doc.new_page(width=fmt.width, height=fmt.height)
        page.show_pdf_page(page.rect, src, ipage.number)
        page.set_rotation(rotation)
    src.close()
    doc.save('test/out.pdf')
    #doc.save(pdf_file.parent/f"{pdf_file.stem}_resized.pdf")
    doc.close()
    return
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf_file', help='PDF file to resize', default='working/manhattan_project/MDH-B1V04C12-General-Aux-National_Bureau_of_Standards.pdf')
    parser.add_argument('--output_file', help='Output file', default='test/output_resized.pdf')
    parser.add_argument('--width', help='Width', default=595)
    parser.add_argument('--height', help='Height', default=842)
    args = parser.parse_args()
    pdf_file = args.pdf_file
    output_file = args.output_file
    width = args.width
    height = args.height

    resize_unevenly_sized_pages(pdf_file, output_file, width, height)
    print(f"Resized {pdf_file} to {output_file}")