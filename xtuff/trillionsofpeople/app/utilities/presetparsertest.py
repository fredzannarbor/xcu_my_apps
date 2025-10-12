import pandas as pd


def presets_parser(preset_filename):

    openfile = "/Users/fred/bin/nimble/openai/nimbleAI/app/presets/" + preset_filename + ".json"
    print(openfile)

    presetsdf = pd.read_json(openfile)
    print(presetsdf)

    presetsdf['preset_name'] = presetsdf.get('preset_name', "Presets")
    presetsdf['preset_pagetype'] = presetsdf.get('preset_pagetype', "UserPrompt")
    presetsdf['preset_description'] = presetsdf.get('preset_description', "Description of this preset.")
    presetsdf['preset_instructions'] = presetsdf.get('preset_instructions', "Fill in the form.")
    presetsdf['preset_additional_notes'] = presetsdf.get('preset_additional_notes', "Notes:")
    presetsdf['pre_user_input'] = presetsdf.get('pre_user_input', "")
    presetsdf['prompt'] = presetsdf.get('prompt', "")
    presetsdf['post_user_input'] = presetsdf.get('post_user_input',"")
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
    presetsdf['file'] = presetsdf.get('answerhandle',"")
    presetsdf['examples_context'] = presetsdf.get('examples_context', "In 2017, U.S. life expectancy was 78.6 years.")
    presetsdf['examples'] = presetsdf.get('examples', '[["What is human life expectancy in the United States?", "78 years."]]')
    presetsdf['max_rerank'] = presetsdf.get('max_rerank', 10)

    return(presetsdf)

    # read pandas values into Python variables
    
    print( preset_name, preset_description, preset_instructions, preset_additional_notes, placeholder, pre_user_input, post_user_input, prompt, engine, temperature, max_tokens, top_p , fp, pp, stop_sequence, echo_on, preset_pagetype, preset_db)
    
    return  preset_name, preset_description, preset_instructions, preset_additional_notes, placeholder, pre_user_input, post_user_input, prompt, engine, temperature, max_tokens, top_p , fp, pp, stop_sequence, echo_on, preset_pagetype, preset_db

if __name__ == '__main__':
    presets_filename = "create-subject-line"
    presetsdf = presets_parser(presets_filename)
    transposed_df = presetsdf.set_index('preset_name').transpose()
    #print(pd.DataFrame.to_string(transposed_df))
    print(transposed_df)