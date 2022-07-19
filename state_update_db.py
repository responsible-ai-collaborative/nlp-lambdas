# state_update_db.py - updates (or generates) embeddings
#                      for reports and incidents
#                      and stores them in the database.
#
# Requires:          - the Longformer submodule is downloaded,
#                    - environment variable MONGODB_CONNECTION_STRING 
#                      set to read the database.
#
# Assumes:           - being executed from project root directory

from os import ( environ, path )
from ast import literal_eval
from pandas import read_csv, DataFrame, concat, array
from pymongo import MongoClient
from torch import tensor
from transformers import LongformerTokenizer, LongformerModel

MONGODB_URI = environ['MONGODB_CONNECTION_STRING']
MODEL_PATH = path.join('inference', 'model')

# Get the Longformer tokenizer and model
tokenizer = LongformerTokenizer.from_pretrained(
    MODEL_PATH,
    local_files_only=True,
    model_max_length=2000
)

model = LongformerModel.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)


# Process the text of one report and return the CLS token
def cls_token(text):
    inp = tokenizer(text,
                    padding='longest',
                    truncation='longest_first',
                    return_tensors='pt')
    return model(**inp).last_hidden_state[0][0]


# Aggregate the incident_id and text 
# of all reports from Mongo for each incident
client = MongoClient(MONGODB_URI)
db = client['aiidprod']
pipeline = [
    {   '$project': {
          '_id': False, 
          'incident_id': True, 
          'reports': True, 
          'embedding': True
        }
    },
    {   '$lookup': {
            'from': 'reports',
            'localField': 'reports',
            'foreignField': 'report_number',
            'pipeline': [
                {   '$project': {
                        '_id': False,
                        'text': True,
                        'report_number': True, 
                        'embedding': True
                    }
                }
            ],
            'as': 'reports'
        }
    }
]

# Update the state using the results
for i, incident in enumerate(db.incidents.aggregate(pipeline)):
    print('checking', incident['incident_id']) # DEBUG

    new_report_embedding = False

    # Update the embeddings of new reports
    # and reports where the text has changed
    for report in incident['reports']:
        print('checking report', report['report_number'])
        text_hash = report['text'][0:20] # TODO: Use a better hash function
        if not (
            report.get('embedding') and 
            report['embedding']['from_text_hash'] == text_hash
        ):
            new_report_embedding = True
            print('Updating embedding')
            token = cls_token(report['text'])
            del report['text']
            report['embedding'] = { 
                'vector': token.detach().tolist(),
                'from_text_hash': text_hash
            }
            db.reports.update_one(
                { 'report_number' : report['report_number'] },
                { '$set': { 'embedding': report['embedding'] } }
            )

    # Store the new mean for each incident
    mean = incident['reports'][0]['embedding']['vector']
    if new_report_embedding:
        count = 1
        for report in incident['reports'][1:]:
            mean = tensor(report['embedding']['vector'])
                       .add(tensor(mean), alpha=count)
                       .div(count + 1)
                       .detach()
                       .tolist()
            count += 1

    report_ids = [r['report_number'] for r in incident['reports']]
    if (
        (not 'embedding' in incident) or 
        report_ids != incident['embedding']['from_reports']
    ):
        print('uploading embedding for incident', incident['incident_id']), 
        db.incidents.update_one(
            { 'incident_id' : incident['incident_id'] },
            { '$set': {
                    'embedding': {
                        'vector': mean,
                        'from_reports': [
                          report['report_number'] 
                          for report in incident['reports']
                        ]
                    }
                }
            }
        )

