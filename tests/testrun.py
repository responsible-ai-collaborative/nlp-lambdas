import subprocess
import json
import ast
import argparse
import sys
import time

# inputs are expectIncident number and a .\docs .json file path
def runTest(expectIncident, docsJson):
    cmd = ['sam', 'local', 'invoke','similar', '-t', './cdk.out/AiidNlpLambdaStack.template.json', '-e', docsJson]

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
 
# inputs are expectIncident number and a .\docs .json file path
#   (runs w/o redirecting output and err to files)
def runTestPipeTest(expectIncident, docsJsonPath):
    # Define command for subprocess
    cmd = ['sam', 'local', 'invoke', 'similar', '-t', './cdk.out/AiidNlpLambdaStack.template.json', '-e', docsJsonPath]

    # Spawn subprocess and wait for its complete stdout (depending on DefaultShell argument)
    print(cmd)
    p = subprocess.Popen(' '.join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
    stdout, err = p.communicate()
    time.sleep(15)

    print("stdout: ", json.loads(stdout))
    print("stderr: ", err)

    # Wait for completion
    while p.poll() == None: continue
    bestID = None

    # Normal execution
    if (p.poll() == 0):
        data = {}
        try:
            data = json.loads(json.loads(stdout))
        except:
            raise Exception('Failure in json parsing')

        try:
            if(data["statusCode"] == 200):
                listoftupals = ast.literal_eval(data['body']['msg'])
                bestID = listoftupals[0][1]
                print("bestID output: ", bestID)
        except:
            raise Exception("Error in reading SAM output, stderr: ", err)
    else:
        raise Exception("Error in SAM execution, exit code: ", p.poll())

    return(expectIncident == bestID)

def main():
    # Initialize parser
    parser = argparse.ArgumentParser()
    
    # Adding optional argument
    parser.add_argument("-i", "--ExpectIncidentNumber", type = int, help = "Give an Expect Incident Id number")
    parser.add_argument("-d", "--DocsJson", help = "Give a .\docs .json file path")
    
    # Read arguments from command lineW
    args = parser.parse_args()

    if args.ExpectIncidentNumber and args.DocsJson:
        sys.exit(not runTestPipeTest(args.ExpectIncidentNumber, args.DocsJson))
        # return runTest(args.ExpectIncidentNumber, args.DocsJson)

if __name__ == "__main__":
   main()
