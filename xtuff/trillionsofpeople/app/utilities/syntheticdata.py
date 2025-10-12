# class for creating unstructured synthetic data
# data types include CRM, knowledge_base, forum, cast_of_characters
# each data type has a config file that specifies its fields
# and the functions used to create each field
import json

class SyntheticData:

    def __init__(self, category_name, config_file):
        self.category_name = category_name
        self.config_file = config_file
        self.config = {}
        print(config_file)
       
        self.load_config()
        self.load_fields()
       # self.load_data()

    def load_config(self):
        with open(self.config_file, 'r') as f:
            self.config = json.load(f)

    def load_fields(self):
        self.fields_array = {}
        for i in range(len(self.config['applications_supported'])):
            self.fields_array['category_name'] = self.config['applications_supported']
            self.fields = []
            
            for field in self.config['applications_supported'][i]['fields']:
                
                self.fields.append(field)
                #print(field)
            self.fields_array['fields'] = self.fields
        #print('fields_array', self.fields_array)
        

    def load_data(self):
        self.data = []
        for item in self.config['data']:
            self.data.append(self.create_field(item))

    def create_field(self, item):
        field = {}
        for key in item:
            if key in self.fields:
                field[key] = self.fields[key]['function'](item[key])
        return field

    def save_data(self):
        with open(self.category_name + '.json', 'w') as f:
            json.dump(self.data, f)

    def json_extract(obj, key):
        """Recursively fetch values from nested JSON."""
        arr = []

        def extract(obj, arr, key):
            """Recursively search for values of key in JSON tree."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        extract(v, arr, key)
                    elif k == key:
                        arr.append(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract(item, arr, key)
            return arr

        values = extract(obj, arr, key)
        return values
# init main
