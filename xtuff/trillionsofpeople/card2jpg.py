# card2jpg

# convert html table to nice looking image
# add language model text
# add image
# add border

from html2image import Html2Image
hti = Html2Image()

def html2jpg(html, output_file):
    hti.screenshot(html_str=html, save_as=output_file)
    return output_file
