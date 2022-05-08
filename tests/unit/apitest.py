import requests
import ast
import subprocess
import json
import argparse
import time
import sys

def apiTestRun(expectIncident, docsJsonPath):
     # start the api
        cmd = ['sam', 'local', 'start-api', '-t', '.\cdk.out\AiidNlpLambdaStack.template.json']

        p = subprocess.Popen(' '.join(cmd), shell=True)
        time.sleep(10)

        with open(docsJsonPath, encoding="utf-8") as json_file:
            json_payload = json.load(json_file)
            get_payload = json_payload['text']
            res = requests.post("http://127.0.0.1:3000/similar", json=json_payload)
            postOutputIncident = ast.literal_eval(json.loads(res.text)['body']['msg'])[0][1]
            print(postOutputIncident)

            get_url = ("http://127.0.0.1:3000/similar?text=\\\"" + get_payload + "\\\"")
            print(get_url)
            res = requests.get(get_url)
            getOutputIncident = ast.literal_eval(json.loads(res.text)['body']['msg'])[0][1]
            print(getOutputIncident)

        p.kill()
        return(getOutputIncident == postOutputIncident == expectIncident)


def main():
     # Initialize parser
    parser = argparse.ArgumentParser()
    
    # Adding optional argument
    parser.add_argument("-i", "--ExpectIncidentNumber", type = int, help = "Give an Expect Incident Id number")
    parser.add_argument("-d", "--DocsJson", help = "Give a .\docs .json file path")
    
    # Read arguments from command lineW
    args = parser.parse_args()

    if args.ExpectIncidentNumber and args.DocsJson:
        sys.exit(not apiTestRun(args.ExpectIncidentNumber, args.DocsJson))


if __name__ == "__main__":
   main()