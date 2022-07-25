# Imports
from ast import literal_eval
import os
import json
import pandas as pd
import torch
from transformers import LongformerTokenizer, LongformerModel
from unidecode import unidecode
import pandas as pd
from typing import Union
from sys import argv, stdin
from hashlib import sha1

model_location = (
    os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'model'
    if '--local' in argv
    else '/function/model'
)

# Load tokenizer and model from local, pretrained model files
tokenizer = LongformerTokenizer.from_pretrained( model_location,
                                                 local_files_only=True,
                                                 model_max_length=2000 )

model = LongformerModel.from_pretrained(model_location, local_files_only=True)

# Get longformer embedding
def get_embedding(text:str):
    inp = tokenizer(text,\
                    padding="longest",\
                    truncation="longest_first",\
                    return_tensors="pt")
    return model(**inp).last_hidden_state[0][0]

# Define lambda handler
def handler(event, context):
    # Starting point for response formatting
    result = {
        "isBase64Encoded": False,
        "statusCode": 500,
        "headers": {"Content-Type": "application/json"},
        "multiValueHeaders": {},
        "body": {"warnings": []}
    }

    # Get input from body or query string
    if ('text' in event):
        event_text = event['text']
    elif ('body' in event and event['body'] != '' and 'text' in json.loads(event['body'])):
        event_text = json.loads(event['body'])['text']
    elif ('queryStringParameters' in event and 'text' in event['queryStringParameters']):
        event_text = event['queryStringParameters']['text']
    else:
        result['statusCode'] = 500
        result['body'] = {'msg': 'Error! Valid input text not provided!'}
        result['headers']['Content-Type'] = "application/json"
        return json.dumps(result)

    # Handle unicode in event_text
    event_text = unidecode(event_text)

    # Found event_text, use it and return result
    try:
        result['statusCode'] = 200
        result['msg'] = 'Success'
        result['body']['embedding'] = {
          'vector': get_embedding(event_text).detach().tolist(),
          'from_text_hash': sha1(event_text.encode('utf-8')).hexdigest()
        }
        result['headers']['Content-Type'] = "application/json"
    except:
        result['statusCode'] = 500
        result['body']['warnings'].append("Error occurred while processing input text!")
        result['headers']['Content-Type'] = "application/json"
    return json.dumps(result)

if '--local' in argv:
    print(handler({'body': json.dumps({'text': stdin.read()})}, None))
