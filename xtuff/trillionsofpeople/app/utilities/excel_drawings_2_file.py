from openpyxl import load_workbook

file = '/Users/fred/unity/app/data/mal-excel/REVIEWED_9_IJN_GUNBOATS.xlsx'


# Load your workbook and sheet as you want, for example
wb = load_workbook(file)
sheet = wb['1']

# find drawings in sheet
drawings = sheet._drawing
print(sheet._rels)
images =  sheet._images
for i in images:
    print(i.format, i.height, i.width, i.path, i._id)


