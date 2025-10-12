#!/usr/bin/python


def bookjson2dict(filename):
    bookdict ={}
    with open(filename, 'r') as f:
        bookdict = json.load(f)
        f.close()
    return bookdict

def create_document(basename, output_dir, working_dir, basedocx=None):
    if basedocx:
        document = Document(basedocx)
    else:
        document = Document()
        try:
            for text in text_list:   #rint(text)
                document.add_paragraph(text)
        except Exception as e:
            print(e, 'error in texts2docx')
        document.save(os.path.join(output_dir, docx_filename))
        
    return document
    
def bookdict2docx(bookdict, document): # or metadatas

    # set up document
        section = document.sections[4]
        header = section.header
        paragraph = header.paragraphs[0]
        paragraph.text = line
        
    # loop through dict and insert in  docx

        for paragraph in document.paragraphs:

            if "Frontmatter Here" in paragraph.text:
                print('found frontmatter')
                for part, content in frontmatter.items():
                    paragraph.insert_paragraph_before(part, style='Heading1')
                    paragraph.insert_paragraph_before(content, style='Normal')

            else:
                pass

                document.save(filename + '.docx')
