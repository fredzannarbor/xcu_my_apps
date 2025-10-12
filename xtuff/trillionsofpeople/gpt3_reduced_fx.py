# gpt3 completion object
import streamlit as st
import json

from datetime import datetime, timedelta
from pprint import pprint
import stripe
import os
import uuid
import re
from os import environ as osenv
import glob

from traceback import TracebackException


stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "price_id": os.environ["STRIPE_PRICE_ID"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
}

stripe.api_key = stripe_keys["secret_key"]

import openai

openai.api_key = st.secrets['OPENAI_API_KEY']
openai_user_id_for_safety_tracking = os.environ['OPENAI_USER_ID_FOR_SAFETY_TRACKING']

import pandas as pd

import docx

from flask_user import current_user

from sqlalchemy import func, extract
from sqlalchemy.dialects import postgresql

#from .s2orc.doc2json.pdf2json.process_pdf import process_pdf_file

import sqlite3
URI_SQLITE_DB = osenv.get('URI_SQLITE_DB')
if URI_SQLITE_DB:
    print('sqlite db is', URI_SQLITE_DB)
else:
    print('no sqlite db')
    st.write('no sqlite db')

def presets_parser(preset_filename):
    print(preset_filename)
    openfile = "app/presets/" + preset_filename + ".json"
    print('opening file', openfile)

    presetsdf = pd.read_json(openfile, dtype=object)
    #presetsdfprint(presetsdf)

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
    presetsdf['finetune_model'] = presetsdf.get('finetune_model', "")
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
    #print('transposeddf', transposed_df)

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
    finetune_model = presetsdf['finetune_model'][0]
    temperature = presetsdf['temperature'][0]
    max_tokens = presetsdf['max_tokens'][0]
    top_p = presetsdf['top_p'][0]
    fp = int(presetsdf['fp'][0])
    pp = presetsdf['pp'][0]
    stop_sequence = presetsdf['stop_sequence'][0]
    if presetsdf['echo_on'][0] == 'True':
        echo_on = True
    else:
        echo_on = False

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

    return presetsdf, preset_name, preset_description, preset_instructions, preset_additional_notes, preset_placeholder, pre_user_input, post_user_input, prompt, engine, finetune_model, temperature, max_tokens, top_p, fp, pp, stop_sequence, echo_on, preset_pagetype, preset_db, user, organization

def construct_preset_dict_for_UI_object(list_of_presets):
    print("constructing preset dict for UI object")
    print("list_of_presets", list_of_presets)
    preset_dir = "app/presets/"
    dict_of_presets_for_UI_object = {}
    list_for_object = []
    for i, preset in enumerate(list_of_presets):
        print('looping over presets', i)
        this_preset_file = preset_dir + preset + ".json"
        print('adding', this_preset_file)
        with open(this_preset_file, 'rb') as f:
            this_preset = json.load(f)
            print(this_preset)
            this_preset_df = pd.DataFrame(this_preset)
            row = [preset, this_preset_df['preset_name'].iloc[0]]
            print('row', row)
            list_for_object.append(row)

            dict_of_presets_for_UI_object = dict(list_for_object)
    print("list_for_object", list_for_object)
    print('dict of presets', dict_of_presets_for_UI_object)
    return dict_of_presets_for_UI_object

def gpt3complete(preset_filename, prompt, username="guest"):
    override_prompt = None
    openai_user_id_for_safety_tracking = os.environ['OPENAI_USER_ID_FOR_SAFETY_TRACKING']

    if prompt:
        override_prompt = prompt

    presetsdf, preset_name, preset_description, preset_instructions, preset_additional_notes, preset_placeholder, pre_user_input, post_user_input, prompt, engine, finetune_model, temperature, max_tokens, top_p, fp, pp, stop_sequence, echo_on, preset_pagetype, preset_db, user, organization = presets_parser(preset_filename)

    print(presetsdf.transpose())

    print("echo on is", echo_on)

    if override_prompt:
        prompt = override_prompt
    print('override prompt is', prompt)

    promptsubmit = pre_user_input + prompt + post_user_input

    print('promptsubmit is:', promptsubmit)

    if openai_user_id_for_safety_tracking is None:
        openai_user_id_for_safety_tracking = str(current_user.id)

    for item in promptsubmit:
        promptchar= len(promptsubmit)

        response = openai.Completion.create(
            engine=engine,
            prompt=promptsubmit,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=fp,
            presence_penalty=pp,
            logprobs=0,
            echo=False,
            user=openai_user_id_for_safety_tracking
        )
        response_text = "#### " + presetsdf['completion_heading'][0] + '\n'
        response_text = response_text + response['choices'][0]['text']

        totaltokens = sum(len(i.split()) for i in response['choices'][0]['logprobs']['tokens'])
        print('totaltokens', totaltokens)
        created_on = datetime.utcnow()
        
        # try:  # this is working
        #     user_id = get_user_id_for_username(username)
        #     print(user_id, totaltokens, created_on)

        #     conn = sqlite3.connect(URI_SQLITE_DB, check_same_thread=False)
        #     c = conn.cursor()
        #     c.execute("INSERT INTO tokens (user_id, totaltokens, created_on) VALUES (?, ?, ?)", (user_id, totaltokens, created_on))
        #     conn.commit()
        #     c.execute("INSERT INTO transactions (user_id, totaltokens, pre_user_input, user_input, post_user_input, prompt, engine, response, safety_rating, created_on) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, totaltokens, pre_user_input, promptsubmit, post_user_input, promptsubmit, str(engine), str(response_text), "NaN", created_on))
        #     conn.commit()

        # except ValueError:
        #     st.write(ValueError)
        #     st.error("Error: ValueError")

        safety_engine = "content-filter-alpha-c4"
        submit = "<|endoftext|>" +  response['choices'][0]['text'] + "\n--\nLabel:"
        print('>>> submitting safety request')
        safety_response = openai.Completion.create(engine=safety_engine, prompt=submit, max_tokens=1, temperature=0, top_p=0, user=openai_user_id_for_safety_tracking)
        
        safety = str(safety_response['choices'][0]['text'])
        print('>>> safety value', safety)
        #print(safety_response)
        totaltokens = 1
        print('totaltokens', totaltokens)
        created_on = datetime.utcnow()

        # try: # this is working

        #     c.execute("INSERT INTO transactions (user_id, totaltokens, pre_user_input, user_input, post_user_input, prompt, engine, response, safety_rating, created_on) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, totaltokens, pre_user_input, promptsubmit, post_user_input, submit, safety_engine, safety, safety, created_on))
        #     conn.commit()
        # except ValueError:
        #     st.write(ValueError)
        #     st.error("Error: ValueError")

        #if quotastatus is None:
        #    quotastatus = 0
        user_id = 37
        #underquota, quotastatus, quotalimit, product = prepare_quotastatus(user_id)
        quotastatus = True
        print(quotastatus, 'quotastatus')
        quotastatus = True
        response = [response, totaltokens, quotastatus, safety]
        
        return response
        # remember that this change breaks the return function to all apps calling this library -- they must select the list item they want


def jsonl2openai(filename):
    searchhandle = openai.File.create(file=open(filename), purpose="search")
    answershandle = openai.File.create(file=open(filename), purpose="answers")
    return searchhandle, answershandle

def docx2jsonl(filename):

    doc = docx.Document(filename)
    data = []

    basename = os.path.splitext(os.path.basename(filename))[0]
    print(basename)
    jsonlfilename = 'app/userdocs/' + str(current_user.id) + '/' + basename + '.jsonl'

    for p in doc.paragraphs:
        data.append(p.text)
       
    df = pd.DataFrame(data, columns=["text"])
    df.to_json(jsonlfilename, orient="records", lines=True)
    return jsonlfilename

def pdf2jsonl(filename, tempdir, outdir):
    jsonfile = process_pdf_file(filename, tempdir, outdir)
    filepathname = os.path.splitext(filename)
    basename = os.path.splitext(os.path.basename(filename))[0]
    print(basename)
    # prepare filename to save 
    jsonfilename = outdir + '/' + basename + '.json'
    data = json.load(open(jsonfilename))
    df = pd.DataFrame(data['pdf_parse']['body_text'])
    df1 = df[['text']]
    # prepare filename to save modified df
    jsonlfilename = outdir + basename + '.jsonl'
    df1.to_json(jsonlfilename, orient="records", lines=True)
    return jsonlfilename

def find_customer_in_local_db(user_id):
    if URI_SQLITE_DB is None:
        print("URI_SQLITE_DB is None")
        return None
    
    conn = sqlite3.connect(URI_SQLITE_DB, check_same_thread=False)
    try:
        conn = sqlite3.connect(URI_SQLITE_DB, check_same_thread=False)
        print('connecting with', URI_SQLITE_DB)
    except Exception as e:
        print('could not connect with db')

    c = conn.cursor()
    c.execute("SELECT stripeCustomerId FROM customers WHERE user_id = ?", (user_id,))
    stripeCustomerId = c.fetchone()
    #print('stripeCustomerId', stripeCustomerId)

    return stripeCustomerId

def get_user_id_for_username(username):
    if URI_SQLITE_DB is None:
        print("URI_SQLITE_DB is None")
        st.error("Error: No URI_SQLITE_DB")
        return None
    print('in gpt3complete, getting user id for username = ', username)
    try:
        conn = sqlite3.connect(URI_SQLITE_DB, check_same_thread=False)
        print('connecting with', URI_SQLITE_DB)
        c = conn.cursor()
        c.execute("SELECT id FROM USERS WHERE username = ?", (username,))
        row = c.fetchone()
        if row:
            user_id = row[0] # check whether this is the right type of object
            print('user id from row[0]', user_id)
            return user_id
        else:
            print('no user id found')
            return None
    except Exception as e:
        print(e)
        user_id = None
    return user_id

def get_user_id_for_stripe_customer_id(stripeCustomerId):
    if URI_SQLITE_DB is None:
        print("URI_SQLITE_DB is None")
        st.error("Error: No URI_SQLITE_DB")
        return None
    print('in gpt3complete, getting user id for stripe customer id = ', stripeCustomerId)
    try:
        conn = sqlite3.connect(URI_SQLITE_DB, check_same_thread=False)
        print('connecting with', URI_SQLITE_DB)
        c = conn.cursor()
        c.execute("SELECT user_id FROM customers WHERE stripeCustomerId = ?", (stripeCustomerId,))
        row = c.fetchone()
        if row:
            user_id = row[0] 
            print('user id from row[0]', user_id)
            return user_id
        else:
            print('no user id found')
            return None
    except Exception as e:
        print(e)
        user_id = None
    return user_id

def prepare_quotastatus(user_id):
    
    product_dict = {
    'Not Logged In' : { 'quotalimit': 0, 'access_level_entitlement': 0},
    'Guest': {'quotalimit': 0, 'access_level_entitlement': 1},
    'Free': {'quotalimit': 5000, 'access_level_entitlement': 2},
    'Standard': {'quotalimit': 100000, 'access_level_entitlement': 3},
    'Premium': {'quotalimit': 2000000, 'access_level_entitlement': 4},
    'Enterprise': {'quotalimit': 1000000, 'access_level_entitlement': 5}
    }
            
    if URI_SQLITE_DB is None:
        print("URI_SQLITE_DB is None")
        st.error("Error: No URI_SQLITE_DB")
        return None
    print('in gpt3complete, preparing quotastatus for user_id, user id is', user_id)

    plan_id, plan_name = 'Free', 'Free'
    
    # calculate current month
    
    created_on = datetime.utcnow()
    quotastatus = 0 # binding
    firstdaycurrentmonth = datetime.today().replace(day=1)
    filter_after = firstdaycurrentmonth
    print('filter_after', filter_after)

    totaltokens = None # tokens used in current openai call, which is none, until it happens
    c = None
    
    # establish connection to db & look up current token usage
    
    try:
        conn = sqlite3.connect(URI_SQLITE_DB, check_same_thread=False)
        c = conn.cursor()
        qs_row = c.execute("SELECT SUM(totaltokens) FROM tokens WHERE user_id = (?) AND created_on > (?)", (user_id, filter_after))
        qs_row = c.fetchone()
        print(qs_row)
        if qs_row[0] is None:
            quotastatus = 0
            print('quotastatus was None', quotastatus)
        else:
            quotastatus = qs_row[0]
            print('quotastatus was non-zero', quotastatus)

    except Exception as e:
        print(e)
        st.error('Error: could not establish connection to SQL db')
        conn = None
        quotastatus = 0

    print('quotastatus', quotastatus)

    # now that we know how many tokens have been used this month,
    # check local database to see if we think this user_id is current Stripe customer

    stripe_id_listed_in_local_db = find_customer_in_local_db(user_id)
    if stripe_id_listed_in_local_db:

        stripeid2verify = stripe_id_listed_in_local_db[0]
    else:
        stripeid2verify = None
        
    print('stripe id to verify is', stripeid2verify)

    if stripeid2verify:
        customer_status_box = st.empty()
        try:
            customer = stripe.Customer.retrieve(stripeid2verify, expand=['subscriptions'])
            #st.write(customer)
        except Exception as e:
            customer = None
            print("Could not verify with Stripe whether there is a customer id with Stripe", e)
            st.info("Could not verify whether this user has a valid customer id, possibly because of a technical issue.  If you think this is in error and you are a valid paying customer, contact support @ nimblebooks.com. In the meantime, you can use all features that are normally available to registered users.")
            # assign a default access level to unknown 
            plan_id, plan_name, access_level_entitlement = 'Free', 'Free', 2

        if customer:
            #st.write("Customer record retrieved from Stripe")
            print("Customer ID is", customer['id'])
            stripeSubscriptionId = customer['subscriptions']['data'][0]['id']
            print('stripeSubscriptionId', stripeSubscriptionId)
            #st.write("Stripe Subscription ID is", stripeSubscriptionId)
            # check whether subscription is valid
            subscription_active = customer['subscriptions']['data'][0]['items']['data'][0]['plan']['active']
            print('subscription_active = ', subscription_active)

            if subscription_active:
                plan_id = customer['subscriptions']['data'][0]['items']['data'][0]['plan']['id']
                plan_name = customer['subscriptions']['data'][0]['items']['data'][0]['plan']['nickname']
                status_box_message = "Your subscription is active. Your plan is " + plan_name + "."
            else:

                status_box_message = "Your subscription exists, but is not active. If you wish to reactivate, please contact support @ nimblebooks.com and provide the subscription id: " + stripeSubscriptionId + "."
                plan_id, plan_name, access_level_entitlement = 'Free', 'Free', 2
            customer_status_box.info(status_box_message)
    else: #no stripeid2verify
        plan_id, plan_name, access_level_entitlement = 'Free', 'Free', 2
        product = plan_id, plan_name, access_level_entitlement

    # consult product dict to see the user's feature entitlements

    access_level_entitlement = product_dict[plan_id]['access_level_entitlement']
    print('access_level_entitlement', access_level_entitlement)
    product = (plan_id, plan_name, access_level_entitlement)
    print('product', product)
    quotalimit = product_dict[plan_id]['quotalimit']
    print('quotalimit', quotalimit)
    print('quotastatus', quotastatus)
    if  quotastatus <= quotalimit:
        underquota = True
    else:
        underquota = False
    if conn:
        conn.close()
    else:
        print('conn is None')
        
    print('underquota', underquota)
    
    product = (plan_id, plan_name, access_level_entitlement)
    return underquota, quotastatus, quotalimit, product
        
def create_uuid():
    return str(uuid.uuid4())

def post_process_text(text, options="all"):
    #all_patterns = [r'<br\s*?>', r'<br>', r'<li>', r'\n\s*\n', r'^-\s+', r'^-', r'\d+[)]'
    #combined_patterns =  = r'|'.join(map(r'(?:{})'.format, all_pats))
    text = text.replace('<br\\s*?>', '')
    text = text.replace('<br>', '\n')
    text = text.replace('<li>', '\n')
    text = re.sub(r'\d+[)]', "", text)
    text = text.replace('\n-', '\n')
    text = text.replace('\n• ','\n')
    text = text.replace('\n ', '\n')
    text = re.sub('[\n]+', '\n', text)
    text = re.sub('\\d+[.]\\s+', '', text).rstrip()
    text = re.sub('\\d+[.\n]\\s+', '', text).rstrip()
    text = text.replace('\\n', '\n')
    text = re.sub('[\n]+', '\n', text)
    text = text.replace('###', '\n\n')
    print('post processed text is', '\n' + text)
    return text

