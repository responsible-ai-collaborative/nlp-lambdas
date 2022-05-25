# state_update.py - updates (or generates) the adjacent state.csv with the current state of the AIID DB.
# Requires:     the Longformer submodule is downloaded,
#               environment variable MONGODB_CONNECTION_STRING set to read the database.
# Assumes:      being executed from project root directory

from os import ( environ, path )
from ast import literal_eval
from pandas import read_csv, DataFrame, concat, array
from pymongo import MongoClient
from torch import tensor
from transformers import LongformerTokenizer, LongformerModel


STATE_DOC = path.join('inference', 'db_state', 'state.csv')
MONGODB_URI = environ['MONGODB_CONNECTION_STRING']
MODEL_PATH = path.join('inference', 'model')

# Get the Longformer tokenizer and model
tokenizer = LongformerTokenizer.from_pretrained(MODEL_PATH,
                                                local_files_only=True,
                                                model_max_length=4096)
model = LongformerModel.from_pretrained(MODEL_PATH, local_files_only=True)


# Process the text of one report and return the CLS token
def cls_token(text):
    inp = tokenizer(text,
                    padding='longest',
                    truncation='longest_first',
                    return_tensors='pt')
    return model(**inp).last_hidden_state[0][0]


# Get the incident_id, count, and current mean from state.csv for each incident
try:
    state = read_csv(STATE_DOC,
                    converters={'mean': literal_eval}).set_index('incident_id')
except FileNotFoundError:
    state = DataFrame({'incident_id': [],
                       'count': [],
                       'mean': []}).set_index('incident_id')

# Aggregate the incident_id and text of all reports from Mongo for each incident
client = MongoClient(MONGODB_URI)
db = client['aiidprod']
collection = db.incidents
pipeline = [
    {'$project': {'_id': False, 'incident_id': True, 'reports': True}},
    {'$lookup': {
        'from': 'reports',
        'localField': 'reports',
        'foreignField': 'report_number',
        'pipeline': [
            {'$project': {'_id': False, 'text': True, 'report_number': True}}
        ],
        'as': 'reports'
    }}
]
results = [result for result in collection.aggregate(pipeline)]

# Update the state using the results
for result in results:
    print('checking', result['incident_id']) # DEBUG

    # Process the first report and store a row for incidents not in the state
    if result['incident_id'] not in state.index:
        token = cls_token(result['reports'][0]['text'])
        row = DataFrame({'count': [1], 'mean': [token.detach().tolist()]},
                        index=[result['incident_id']])
        state = concat([state, row])
        print('added incident') # DEBUG

    # Process the text of new reports, and store new mean for each incident
    count = int(state.loc[result['incident_id'], 'count'])
    for report in result['reports'][count:]:
        print('adding report', report['report_number'], 'count', count) # DEBUG
        token = cls_token(report['text'])
        mean = tensor(state.loc[result['incident_id'], 'mean'])
        new = token.add(mean, alpha=count).div(count + 1).detach().tolist()
        count += 1
        state.loc[result['incident_id'],
                  ['count', 'mean']] = array([count, new], dtype=object)

# Save the state back to the .csv file
state.index.rename('incident_id', inplace=True)
state = state.sort_values(by='incident_id')
state.to_csv(STATE_DOC)
