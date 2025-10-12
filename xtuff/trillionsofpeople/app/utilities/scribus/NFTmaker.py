# creates NFT in Scribus

import scribus
from scribus import *
import json
#from check_scribus_environment import is_venv

#venv_status = is_venv()

scribus.newDocument(PAPER_A6, (3, 3, 3, 3), PORTRAIT, 1, UNIT_POINTS, PAGE_2, 0, 2)

def create_colors():

    DominantColor = "Nimble Blue"
    InvertedColor = "White"

    ImageFileName = "placeholder.png"

    return DominantColor, InvertedColor

def create_layers():

    scribus.createLayer('Steganography')
    scribus.createLayer('Images')
    scribus.createLayer('Text')
    scribus.createLayer('Decorations')

    return

def create_styles(basefont="Futura Medium", basefontsize=10.0, DominantColor="Black", InvertedColor="Black"):
    BaseFont = basefont
    BaseFontSize = basefontsize

    createCharStyle(name="Title 1", font=BaseFont,
                    fontsize=48, features='smallcaps', fillcolor=InvertedColor)
    createParagraphStyle("Title1", linespacingmode=1,
                        alignment=1, charstyle="Title 1")

    createCharStyle(name="SubTitle", font=BaseFont,
                    fontsize=36, features='smallcaps', fillcolor=InvertedColor)
    createParagraphStyle("SubTitle", linespacingmode=1,
                        alignment=1, charstyle="SubTitle")

    createCharStyle(name="Category", font=BaseFont,
                    fontsize=basefontsize, features='smallcaps', fillcolor=InvertedColor)
    createParagraphStyle("Byline", linespacingmode=1,
                        alignment=1, charstyle="Byline")

    createCharStyle(name="Body Text", font=BaseFont,
                    fontsize=11, features='none', fillcolor=DominantColor)
    createParagraphStyle("Body Text", linespacingmode=1,
                        alignment=3, charstyle="Body Text")

    createCharStyle(name="Picture Caption", font=BaseFont,
                    fontsize=11, features='none', fillcolor=InvertedColor)
    createParagraphStyle("Picture Caption", linespacingmode=1,
                        alignment=2, charstyle="Picture Caption")

    return


def applyStyle(style, story):

    '''Try to apply style to selected text. If style doesn't exist, create it.'''

    try:

        setStyle(style, story)

    except:

        createParagraphStyle(style)

        setStyle(style, story)

    return story


def create_text_frames():
    return

def create_image_frames():
    
    return

def read_text_content(jsonfilename):
    with open(jsonfilename, 'r') as f:
        data = json.load(f)
    return data

def load_images(image_list):
    for image in image_list:
        scribus_images = scribus.loadImage(image)
    return

def SelectAllText(textframe): 
    texlen = scribus.getTextLength(textframe) 
    scribus.selectText(0,texlen,textframe) 
    return

def insert_text_content(data):

    y = 50
    scribus.createText(3,y,296,371,"Data")
    scribus.selectObject("Data")
    for key, value in data.items():
        len_key = len(key)
        scribus.insertText(key, -1)
        scribus.selectText(len_key, -1)
        scribus.setCharacterStyle("Category")
        scribus.insertText(value, -1, "Data")
        SelectAllText("Data")
        scribus.setParagraphStyle("Body Text", "Data")
    scribus.deselectAll()
        


    return

def insert_images(scribus_images):
    return

def save_doc_as_image():
    i = ImageExport()
    i.type = 'JPG' # select one from i.allTypes list
    i.scale = 100 # I want to have 200%
    i.name = '/Users/fred/bin/nimble/unity/trillions-deploy/app/data/longform_test/PantheonWave1_aa21/testnft.jpg'
    i.save()


jsonfilename = '/Users/fred/bin/nimble/unity/trillions-deploy/app/data/longform_test/results.json'
create_colors()
create_layers()
create_styles()
data = read_text_content(jsonfilename)
insert_text_content(data)
save_doc_as_image()
