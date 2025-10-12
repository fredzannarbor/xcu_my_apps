import pypandoc


def create_coverpage(title, author, thisdoc_dir='currentdoc'):
    pypandoc.convert_file(thisdoc_dir + '/coverpage.tex', 'pdf', outputfile=thisdoc_dir + '/coverpage.pdf')

except Exception as e:
print(e)

print('coverpage created')
return

create_coverpage('Testing', 'Stephen King')
