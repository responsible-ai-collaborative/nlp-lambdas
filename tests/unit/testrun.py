import subprocess
import json
import ast
import argparse

# inputs are expectIncident number and a .\docs .json file path
def runTest(expectIncident, docsJson):
    cmd = ['sam', 'local', 'invoke','similar', '-t', '.\cdk.out\AiidNlpLambdaStack.template.json', '-e', docsJson]

    with open("stdout.json","wb") as out, open("stderr.txt","wb") as err:
        p = subprocess.Popen(cmd,stdout=out,stderr=err, shell=True)
        p.communicate()


    with open('stdout.json', 'r') as infile, \
        open('output.json', 'w') as outfile:
        data = json.load(infile)
        outfile.write(data)


    with open('output.json') as json_file:
        data = json.load(json_file)

    if(data["statusCode"] == 200):
        listoftupals = ast.literal_eval(data['body']['msg'])
        bestID = listoftupals[0][1]
        print(bestID)
    return(expectIncident == bestID)
 
 
# Initialize parser
parser = argparse.ArgumentParser()
 
# Adding optional argument
parser.add_argument("-i", "--ExpectIncidentNumber", type = int, help = "Give an Expect Incident Id number")
parser.add_argument("-d", "--DocsJson", help = "Give a .\docs .json file path")
 
# Read arguments from command line
args = parser.parse_args()

if args.ExpectIncidentNumber and args.DocsJson:
    print(runTest(args.ExpectIncidentNumber, args.DocsJson))


