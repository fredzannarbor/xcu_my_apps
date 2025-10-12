import pandas as pd

preset_filename = 'create-subject-lines'
openfile = "app/presets/" + preset_filename + ".json"

presetsdf = pd.read_json(openfile)
print(presetsdf)

#search form

presetsdf['preset_name'] = presetsdf.get('preset_name', "Presets")
presetsdf['preset_pagetype'] = presetsdf.get('preset_pagetype', "UserPrompt")
presetsdf['preset_description'] = presetsdf.get('preset_description', "Description of this preset.")
presetsdf['preset_instructions'] = presetsdf.get('preset_instructions', "Fill in the form.")
presetsdf['preset_placeholder'] = presetsdf.get('preset_placeholder', "Enter this text:")
presetsdf['pre_user_input'] = presetsdf.get('pre_user_input', "")
presetsdf['prompt'] = presetsdf.get('prompt', "")
presetsdf['post_user_input'] = presetsdf.get('post_user_input',"")
presetsdf['preset_additional_notes'] = presetsdf.get('preset_additional_notes', "Notes:")

# request parameters

presetsdf['engine'] = presetsdf.get('engine', "ada")
presetsdf['temperature'] = presetsdf.get('temperature', 0.7)
presetsdf['max_tokens'] = presetsdf.get('max_tokens', 100)
presetsdf['top_p'] = presetsdf.get('top_p', 1.0)
presetsdf['fp'] = presetsdf.get('fp', 0.5)
presetsdf['pp'] = presetsdf.get('pp', 0.5)
presetsdf['stop_sequence'] = presetsdf.get('stop_sequence', ["\n", "<|endoftext|>"])
presetsdf['echo_on'] = presetsdf.get('echo_on', False)
presetsdf['search_model'] = presetsdf.get('search_model', "ada")
presetsdf['model'] = presetsdf.get('model', "curie")
presetsdf['question'] =presetsdf.get('question',"")
presetsdf['fileID'] = presetsdf.get('answerhandle',"")
presetsdf['examples_context'] = presetsdf.get('examples_context', "In 2017, U.S. life expectancy was 78.6 years.")
presetsdf['examples'] = presetsdf.get('examples', '[["What is human life expectancy in the United States?", "78 years."]]')
presetsdf['max_rerank'] = presetsdf.get('max_rerank', 10)

# specify secure db for Journals
presetsdf['preset_db'] = presetsdf.get('preset_db', 'None')

# metadata

presetsdf['user'] = presetsdf.get('user', 'testing')
presetsdf['organization'] = presetsdf.get('organization', 'org-M5QFZNLlE3ZfLaRw2vPc79n2') # NimbleAI


# print df for convenience
transposed_df = presetsdf.set_index('preset_name').transpose()
print('transposeddf', transposed_df)

# now read into regular variables

preset_name = presetsdf['preset_name'][0]
preset_pagetype = presetsdf['preset_pagetype'][0]
preset_description  = presetsdf['preset_description'][0]
preset_instructions = presetsdf['preset_instructions'][0]
preset_placeholder = presetsdf['preset_placeholder'][0]
preset_additional_notes =presetsdf['preset_additional_notes'][0]
pre_user_input = presetsdf['pre_user_input'][0]
post_user_input = presetsdf['post_user_input'][0]
prompt = presetsdf['prompt'][0]
engine = presetsdf['engine'][0]
temperature = presetsdf['temperature'][0]
max_tokens = presetsdf['max_tokens'][0]
top_p = presetsdf['top_p'][0]
fp = presetsdf['fp'][0]
pp = presetsdf['pp'][0]
stop_sequence = presetsdf['stop_sequence'][0]
echo_on = presetsdf['echo_on'][0]
search_model = presetsdf['search_model'][0] 
model = presetsdf['model'][0]
question =presetsdf['question'][0]
fileID = presetsdf['fileID'][0] 
examples_context = presetsdf['examples_context'][0]
examples = presetsdf['examples'][0]
max_rerank = presetsdf['max_rerank'][0]
preset_db = presetsdf['preset_db'][0]
user = presetsdf['user'][0]
organization = presetsdf['organization'][0]


# then return both df and regular variables

print (preset_name, preset_description, preset_instructions, preset_additional_notes, preset_placeholder, pre_user_input, post_user_input, prompt, engine, temperature, max_tokens, top_p, fp, pp, stop_sequence, echo_on, preset_pagetype, preset_db, user, organization)
