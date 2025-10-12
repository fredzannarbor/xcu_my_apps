'''
https://ghostscript.readthedocs.io/en/gs10.0.0/VectorDevices.html#creating-a-pdf-x-3-document
'''
import subprocess


def ps2pdfx3(metadatas, postscript_file):
    try:
        subprocess.run(
            ['gs', '-dPDFX', '-dBATCH', '-dNOPAUSE', '-sColorConversionStrategy=CMYK', '-sDEVICE=pdfwrite',
             '-sOutputFile=out-x3.pdf',
             'PDFX_def.ps', postscript_file], check=True)
        metadatas["pdfx3"] = "out-x3.pdf"

    except Exception as e:
        print("error creating PDFX-3" + str(e))
        metadatas["interior_postscript"] = ""

    return metadatas
