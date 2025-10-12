# create class WidgetData


class WidgetData:
    
    def __init__(self, file_path):
        self.file_path = file_path
        
    def listoffiles(self):
        listoffiles = get_filenames(self.file_path)
        self.listoffiles = remove_DS_store(listoffiles)
        return self.listoffiles
        
    def get_filenames(path):
        """
        Select a file from a directory
        """
        files = os.listdir(path)
        if '.DS_Store' in files:
            files.remove('.DS_Store')
        return self.files

    def remove_DS_store(list):
        if '.DS_Store' in list:
            list.remove('.DS_Store')
        return self.list 