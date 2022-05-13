from ast import literal_eval
from pandas import read_csv
import torch
from transformers import LongformerTokenizer, LongformerModel


# You will need to point these at the correct docs.
DATA_DOC = "incidents.csv"
STATE = "state.csv"

# Acquire pre trained tokenizer and model
# TODO: move to local models.
tokenizer = LongformerTokenizer.from_pretrained("allenai/longformer-base-4096")
model = LongformerModel.from_pretrained("allenai/longformer-base-4096")

# Load in a list of articles from a CSV
data = read_csv(DATA_DOC)
state = read_csv(STATE, converters={'mean': literal_eval})


# Process a single text and perform cosine similarity between its CLS token and
# the mean CLS token tensor for each incident. Return the list of these values.
def test(text):
    inp = tokenizer(text,
                    padding="longest",
                    truncation="longest_first",
                    return_tensors="pt")
    out = model(**inp)
    sims = [(torch.nn.functional.cosine_similarity(
                 out.last_hidden_state[0][0],
                 torch.tensor(state.loc[i,"mean"]),
                 dim=-1).item(),
             state.loc[i,"incident_id"]) for i in range(len(state))]
    return sims


# Test every article in the database. If the most similar incident is the right
# one, print the index. Else, print the actual label and best_of best guesses.
texts = data.text.tolist()
ids = data.incident_id.tolist()
intervals = {}
for i in range(len(data)):
    sims = sorted(test(texts[i]), reverse=True)
    for j in range(len(sims)):
        if ids[i] == sims[j][1]:
            if j + 1 not in intervals:
                intervals[j + 1] = 0
            intervals[j + 1] += 1
            mean = sum([k * intervals[k] for k in intervals]) / (i + 1)
            worst = max(intervals)
            print(f"count: {i + 1} mean: {mean} max: {worst} intervals: {intervals}")
            break
    