from os import ( environ, path )
from ast import literal_eval
from pandas import read_csv, DataFrame, concat, array
from pymongo import MongoClient
from torch import tensor
from transformers import LongformerTokenizer, LongformerModel


STATE_DOC = path.join('inference', 'db_state', 'state.csv')
MONGODB_URI = environ['MONGODB_CONNECTION_STRING']

# Get the Longformer tokenizer and model
# TODO: Change to local model
tokenizer = LongformerTokenizer.from_pretrained('allenai/longformer-base-4096')
model = LongformerModel.from_pretrained('allenai/longformer-base-4096')


# Process the text of one report and return the CLS token
def cls_token(text):
    inp = tokenizer(text,
                    padding='longest',
                    truncation='longest_first',
                    return_tensors='pt')
    return model(**inp).last_hidden_state[0][0]


# Get the incident_id, count, and current mean from state.csv for each incident
state = read_csv(STATE_DOC,
                 converters={'mean': literal_eval}).set_index('incident_id')

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
            {'$project': {'_id': False, 'text': True}}
        ],
        'as': 'reports'
    }}
]
results = [result for result in collection.aggregate(pipeline)]

# Update the state using the results
for result in results:
    # print('checking', result['incident_id'])

    # Process the first report and store a row for incidents not in the state
    if result['incident_id'] not in state.index:
        token = cls_token(result['reports'][0]['text'])
        row = DataFrame({'count': [1], 'mean': [token.detach().tolist()]},
                        index=[result['incident_id']])
        state = concat([state, row])
        # print('added incident')

    # Process the text of new reports, and store new mean for each incident
    count = state.loc[result['incident_id'], 'count']
    for report in result['reports'][count:]:
        # print('adding report, count', count)
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
