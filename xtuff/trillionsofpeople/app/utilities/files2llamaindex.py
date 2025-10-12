import os
from pathlib import Path

import pandas as pd
from langchain.chat_models import ChatOpenAI
from llama_index import GPTSimpleVectorIndex, LLMPredictor, download_loader, PromptHelper, ServiceContext, \
    SimpleDirectoryReader, GPTListIndex
from llama_index.node_parser import SimpleNodeParser
from llama_index.readers.file.base import DEFAULT_FILE_EXTRACTOR, ImageParser
from app.utilities.gpt3complete import presets_parser, post_process_text
import os
from pathlib import Path

import pandas as pd
from langchain.chat_models import ChatOpenAI
from llama_index import GPTSimpleVectorIndex, LLMPredictor, download_loader, PromptHelper, ServiceContext, \
    SimpleDirectoryReader, GPTListIndex
from llama_index.node_parser import SimpleNodeParser
from llama_index.readers.file.base import DEFAULT_FILE_EXTRACTOR, ImageParser

from app.utilities.gpt3complete import presets_parser, post_process_text

openai_api_key = os.environ.get('OPENAI_API_KEY')


def set_service_context(llm="ChatOpenAI", temperature=0.0, model_name="gpt-3.5-turbo", max_input_size=3600,
                        num_output=256, max_chunk_overlap=20):
    max_input_size = 3600
    # set number of output tokens
    num_output = 256
    # set maximum chunk overlap
    max_chunk_overlap = 20
    prompt_helper = PromptHelper(max_input_size, num_output, max_chunk_overlap)
    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo",
                                                headers={"Helicone-Cache-Enabled": "False",
                                                         "Helicone-Property-Module": "files2llamaindex"}))
    # add shortname to function signature
    #"Helicone-Property-Shortname": shortname}
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, chunk_size_limit=512)
    #print(f'service context is set: \n {str(service_context.llm_predictor.llm)} etc.')
    return service_context


def get_file_extractor():
    image_parser = ImageParser(keep_image=True, parse_text=True)
    file_extractor = DEFAULT_FILE_EXTRACTOR
    file_extractor.update(
        {
            ".jpg": image_parser,
            ".png": image_parser,
            ".jpeg": image_parser,
        }
    )

    return file_extractor


parser = SimpleNodeParser()


def get_metadatas(thisdoc_dir):
    if os.path.exists(thisdoc_dir + '/metadatas_df.json'):
        print(thisdoc_dir + '/metadatas_df.json exists')
        # load json dictionary as pandas dataframe
        metadatas_df = pd.read_json(thisdoc_dir + '/metadatas_df.json')
        # metadatas_df = pd.DataFrame.from_dict(thisdoc_dir + '/metadatas_df.json')
        print(metadatas_df)
        metadatas = metadatas_df.to_dict('records')[0]
    else:
        print('metadatas.json does not exist, creating empty dictionary')
        metadatas = {}
    return metadatas


def load_text_directory(metadatas, textdir):
    if os.path.exists(textdir + '/index/index.json'):
        print('Directory has already been indexed, loading from cache')
        try:
            textdir_index = GPTSimpleVectorIndex.load_from_disk(textdir + '/index/index.json',
                                                                service_context=metadatas['service_context'])
        except Exception as e:
            print(e)
            return Exception
    else:
        if not os.path.exists(textdir + '/index'):
            os.mkdir(textdir + '/index')
        print('Indexing directory for the first time, this may take a few minutes ...')
        documents = SimpleDirectoryReader(textdir).load_data()
        parser = SimpleNodeParser()
        nodes = parser.get_nodes_from_documents(documents)
        textdir_index = GPTSimpleVectorIndex(nodes, service_context=metadatas['service context'])
        print('Indexing complete')
        textdir_index.save_to_disk(textdir + '/index/index.json')

    return textdir_index


def check_if_index_dir_exists(metadatas, thisdoc_dir):
    index_dir = thisdoc_dir + "/index/"
    if os.path.exists(index_dir):
        print(f'Index directory {index_dir} exists')
        metadatas['index_dir'] = index_dir
        print(f"metadatas['index_dir'] is {metadatas['index_dir']}")
        metadatas['index_dir_status'] = 'Created'
        print(f"metadatas['index_dir_status'] is {metadatas['index_dir_status']}")
        return metadatas, True
    else:
        print('Index directory does not exist, creating it')
        try:
            os.mkdir(index_dir)
            metadatas['index_dir'] = index_dir
            print(f"metadatas['index_dir'] is {metadatas['index_dir']}")
            metadatas['index_dir_status'] = 'created'
            print(f"metadatas['index_dir_status'] is {metadatas['index_dir_status']}")
        except Exception as e:
            print(e)
            metadatas['index_dir'] = str(e)
            metadatas['index_dir_status'] = 'not created'
            print(f"metadatas['index_dir_status'] is {metadatas['index_dir_status']}")
            return metadatas, False
    return metadatas, True


def check_if_indexes_exist(metadatas, thisdoc_dir):
    index_dir = thisdoc_dir + "index/"
    indexes = ['simple_vector_index', 'list_index', 'gpt_index', 'image_index']
    for index in indexes:
        if os.path.exists(index_dir + index + '.json'):
            print(f'{index} exists')
            metadatas[index + '_exists'] = True
        else:
            print(f'{index} does not exist')
            metadatas[index + '_exists'] = False
    return metadatas


def load_or_create_simplevectorindex(metadatas, thisdoc_dir):
    index_dir = thisdoc_dir + "/index"
    service_context = set_service_context()
    metadatas['service context'] = service_context
    if os.path.exists(index_dir + '/simple_vector_index.json'):
        print(f'Loading from cached simple_vector_index in {index_dir}')

        try:
            simple_vector_index = GPTSimpleVectorIndex.load_from_disk(index_dir + '/simple_vector_index.json',
                                                                      service_context=metadatas['service context'])
            print('loaded SVI from disk')
        except Exception as e:
            print("Exception is", e)
            return e
    else:
        print('Vector indexing book for the first time, this may take a few minutes ...')
        JSONReader = download_loader("JSONReader")
        loader = JSONReader()
        parser = SimpleNodeParser()
        try:
            documents = loader.load_data(Path(thisdoc_dir + '/text.json'))
            nodes = parser.get_nodes_from_documents(documents)
            simple_vector_index = GPTSimpleVectorIndex(nodes, service_context=service_context)
            print('Indexing complete')
            simple_vector_index.save_to_disk(index_dir + '/simple_vector_index.json')
        except Exception as e:
            print(e)
            return None
        metadatas['index_dir'] = index_dir
        metadatas['simple_vector_index_exists'] = True
        metadatas['simple_vector_index_struct'] = simple_vector_index.index_struct
        print('completed vector_index')
    return metadatas, simple_vector_index


def load_or_create_gptlistindex(metadatas, thisdoc_dir):
    index_dir = thisdoc_dir + "/index"
    service_context = set_service_context()
    metadatas['service context'] = service_context
    if os.path.exists(index_dir + '/list_index.json'):
        print(f'Loading from cached list_index in {index_dir}')

        try:
            list_index = GPTListIndex.load_from_disk(index_dir + '/list_index.json',
                                                     service_context=metadatas['service context'])
        except Exception as e:
            print("Exception is", e)
            return None
    else:
        print('Indexing book for the first time, this may take a few minutes ...')
        JSONReader = download_loader("JSONReader")
        loader = JSONReader()
        parser = SimpleNodeParser()
        try:
            documents = loader.load_data(Path(thisdoc_dir + '/text.json'))
            nodes = parser.get_nodes_from_documents(documents)
            list_index = GPTListIndex(nodes, service_context=service_context)
            print('Indexing complete')
            list_index.save_to_disk(index_dir + '/list_index.json'
                                    )

        except Exception as e:
            print(e)
            return None
        metadatas['index_dir'] = index_dir
        metadatas['list_index_exists'] = True
        # get index structure
        metadatas['list_index_struct'] = list_index.index_struct
        print('completed create_gptindex')
    return metadatas, list_index


def submit_presets_to_simple_vector_index(metadatas, simple_vector_index, presets, thisdoc_dir):
    service_context = metadatas['service context']
    result_list = []
    if presets:
        actual_responses = []
        for preset in presets:
            presetsdf, preset_name, preset_description, preset_instructions, preset_additional_notes, preset_placeholder, pre_user_input, post_user_input, prompt, engine, suffix, finetune_model, temperature, max_tokens, top_p, fp, pp, stop_sequence, echo_on, preset_pagetype, preset_db, user, organization = presets_parser(
                preset)
            current_presetdf = presets_parser(preset)[0]
            preset_result_df = pd.DataFrame()
            question = pre_user_input + prompt + '\n' + post_user_input
            vector_response = simple_vector_index.query(question, service_context=service_context)
            vector_response_text = vector_response.response
            vector_response_text = post_process_text(vector_response_text)
            completion_heading = f"{current_presetdf['completion_heading'].iloc[0]}"
            append_item = [preset, str(vector_response_text)]
            result_list.append(append_item)
            actual_responses.append(vector_response)
        actual_responses_df = pd.DataFrame(actual_responses)
        actual_responses_df.to_json(f'{thisdoc_dir}/actual_responses.json')
        result_list_df = pd.DataFrame(result_list, columns=['preset', 'response'])
        result_list_df.to_json(f'{thisdoc_dir}/result_list.json')
        result_list_df.to_csv(f'{thisdoc_dir}/result_list.csv', index=False)
        metadatas['result_list'] = result_list
    return metadatas,result_list


def summarize_index(metadatas, index):
    print('entering summarize_index')
    try:
        service_context = metadatas['service context']
    except Exception as e:
        print(f"error is in service context {Exception}")
    try:
        print(service_context, '\n')
        summary = index.query("Please summarize this document in several paragraphs.", response_mode="tree_summarize",
                              service_context=service_context)
    except Exception as e:
        print('error is in index.query', e)
    metadatas['summary response'] = summary.response
    metadatas['llama_summary'] = summary.response
    metadatas['summary sources'] = summary.get_formatted_sources(length=1000)
    return metadatas, summary.response


def query_simple_vector_index(metadatas, simple_vector_index, question):
    service_context = metadatas['service context']
query_simple_vector_index()    response = simple_vector_index.query(question, service_context=service_context)
    return response


def get_single_image_text(metadatas, index_dir, filename):
    service_context = metadatas['service context']

    from pathlib import Path
    read_image_path = Path(index_dir + 'page_images/' + filename)
    ImageReader = download_loader("ImageReader")
    # If the Image has plain text, use text_type = "plain_text"
    loader = ImageReader(text_type="plain_text")
    documents = loader.load_data(file=Path(read_image_path))
    print(documents[0].text)
    nodes = parser.get_nodes_from_documents(documents)
    image_index = GPTListIndex(nodes, service_context=service_context)
    image_index.save_to_disk(index_dir + '/image_index.json')
    response = image_index.query("what is this image?", response_mode="tree_summarize", service_context=service_context)
    return response.response


def load_images_and_scan_for_text(metadatas, thisdoc_dir):
    # load images and scan for text
    Parser = SimpleNodeParser
    service_context = metadatas['service context']
    file_extractor = get_file_extractor()
    page_images_dir = thisdoc_dir + 'page_images'
    img_reader = SimpleDirectoryReader(
        input_dir=page_images_dir, file_extractor=file_extractor
    )
    try:
        print(f'Loading images from {page_images_dir}')
        img_docs = img_reader.load_data(page_images_dir)
    except Exception as e:
        print(e)
        return metadatas, None
    print('number of images is', len(img_docs))

    img_nodes = Parser.get_nodes_from_documents(img_docs)
    image_index = GPTListIndex(img_nodes, service_context=service_context)
    metadatas['image_index'] = image_index
    metadatas['image_index_struct'] = image_index.index_struct
    metadatas['image_index_exists'] = True
    print(image_index.index_struct)
    return metadatas, image_index
    return metadatas, None


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--thisdoc_dir", "-T", type=str, default="output/Logan3pp")
    argparser.add_argument("--question", "-Q", type=str, default="What is the meaning of life?")
    argparser.add_argument("--loader", "-l", type=str, default="JSONReader")
    argparser.add_argument("--metadatas", "-m", type=str, default="metadatas_df.json")
    argparser.add_argument("--ask_question_only", "-A", type=bool, default=True)
    argparser.add_argument("--Helicone-cache-off", "-HC", type=bool, default=True)
    args = argparser.parse_args()
    helicone_cache_off = args.Helicone_cache_off
    ask_question_only = args.ask_question_only
    question = args.question
    loader = args.loader

    # strip any trailing slash from thisdoc_dir
    thisdoc_dir = args.thisdoc_dir.rstrip('/')
    print(f'thisdoc_dir is {thisdoc_dir} without trailing slash')

    # load metadatas object
    metadatas = get_metadatas(args.thisdoc_dir)
    print(type(metadatas))

    metadatas['service context'] = set_service_context
    print(f"service context is {metadatas['service context']}")
    # print(f"metadatas are {metadatas}")

    # now unpack metadatas & get started
    try:
        metadatas['index_dir'] = check_if_index_dir_exists(metadatas, args.thisdoc_dir)
    except Exception as e:
        print(e)

    metadatas = check_if_indexes_exist(metadatas, args.thisdoc_dir)

    #  check if image_index already exists
    if metadatas['image_index_exists']:
        print('Image index already exists')
    else:
        print('Creating image index')
        # image_index_info = load_images_and_scan_for_text(metadatas, args.thisdoc_dir)
        print(args.thisdoc_dir)
        get_single_image_text(metadatas, args.thisdoc_dir, "version2_Page_119.jpg")

    list_index_info = load_or_create_gptlistindex(metadatas, thisdoc_dir)
    metadatas = list_index_info[0]
    list_index = list_index_info[1]

    simple_vector_info = load_or_create_simplevectorindex(metadatas, thisdoc_dir)
    metadatas = simple_vector_info[0]
    simple_vector_info = simple_vector_info[1]

    if 'summary response' in metadatas:
        print('summary response already exists')
    else:
        print('creating summary for the first time')
        summary = summarize_index(metadatas, list_index)
        print(summary[1])

    if args.ask_question_only:
        response = query_simple_vector_index(metadatas, list_index, args.question)
        print(response[1])

    with open(args.thisdoc_dir + '/metadatas_df.json', 'w') as f:
        f.write(metadatas)
# save metadatas
