import glob

from docx import Document

docfile = 'appendix_9_pt_boats.docx'
document = Document(docfile)
core_properties = document.core_properties

for file in glob.glob("*.docx"):
    print('---')
    print(file)
    print(core_properties.revision)
    print(core_properties.last_printed)
    print('last modified', core_properties.modified)

    