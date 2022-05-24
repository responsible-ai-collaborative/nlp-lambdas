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

model = LongformerModel.from_pretrained(
    './inference/model', local_files_only=True)
tokenizer = LongformerTokenizer.from_pretrained(
    './inference/model', local_files_only=True)
csv_path = './inference/db_state/incidents.csv'
incidents_path = './inference/db_state/state.csv'
best_of_def = 3

# Load in a list of incident states from a CSV
state = pd.read_csv(incidents_path, converters={"mean": literal_eval})

# Get longformer embedding
def get_embedding(text:str):
    inp = tokenizer(text,
                    padding="longest",
                    truncation="longest_first",
                    return_tensors="pt")
    return model(**inp).last_hidden_state[0][0]

# Compute cosine similarity between two tensors
# Returns a single value of the cosine_sim
def compute_cosine_sim_e_e(embed_1: torch.Tensor, embed_2: torch.Tensor):
    return torch.nn.functional.cosine_similarity(embed_1, embed_2, dim=-1)

# Compute cosine similarity between a tensor and all embeddings in a db state DataFrame
# Returns a list of tuples (cosine_sim, incident_id) for each incident in dataframe
def compute_cosine_sim_e_df(embed: torch.Tensor, dataframe: pd.DataFrame):
    return [(
                compute_cosine_sim_e_e(embed, torch.tensor(dataframe.loc[i, "mean"])).item(),
                dataframe.loc[i, "incident_id"]
            ) for i in range(len(state))]

# Process input text for text-to-db-similar computation
# Returns a list of the most N (best_of) similar incidents with scores and IDs
def process_input(text: str, best_of: int = best_of_def):
    embed = get_embedding(text)
    cosine_sims = sorted(compute_cosine_sim_e_df(embed, state), reverse=True)
    if (best_of >= 0):
        return cosine_sims[:best_of]
    else:
        return cosine_sims

event_text = ""
incident = 15
with open(f"./tests/unit/testing_materials/lambda_test_request_incident_{incident}.json", "r", encoding="utf-8") as text_json_fp:
    text_json = json.load(text_json_fp)
    text = text_json["text"]
    event_text = unidecode(text[:6000])

embed = get_embedding(event_text)
json_out = {"embed":embed.detach().tolist()}

with open(f"./tests/unit/testing_materials/lambda_test_request_incident_{incident}_embedding.json", "w") as json_file:
    json.dump(json_out, json_file)

print(json_out)

print(compute_cosine_sim_e_e(embed, torch.tensor(json_out["embed"])))
