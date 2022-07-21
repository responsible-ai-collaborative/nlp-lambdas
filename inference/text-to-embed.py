# Imports
from ast import literal_eval
import os
import json
import os
import pandas as pd
import torch
from transformers import LongformerTokenizer, LongformerModel
from unidecode import unidecode
import pandas as pd
from typing import Union

# Load tokenizer and model from local, pretrained model files
tokenizer = LongformerTokenizer.from_pretrained('/function/model',
                                                local_files_only=True,
                                                model_max_length=2000)
model = LongformerModel.from_pretrained('/function/model',
                                        local_files_only=True)

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
        res = get_embedding(event_text)
        result['statusCode'] = 200
        result['body']['msg'] = str(res)
        result['headers']['Content-Type'] = "application/json"
    except:
        result['statusCode'] = 500
        result['body']['warnings'].append("Error occurred while processing input text!")
        result['headers']['Content-Type'] = "application/json"
    return json.dumps(result)

