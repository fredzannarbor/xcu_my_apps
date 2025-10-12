from openpyxl import load_workbook

file = '/Users/fred/unity/app/data/mal-excel/REVIEWED_9_IJN_GUNBOATS.xlsx'


# Load your workbook and sheet as you want, for example
wb = load_workbook(file)
sheet = wb['1']

# find drawings in sheet
drawing = sheet._drawing
images =  sheet._images
print(drawing, images)



