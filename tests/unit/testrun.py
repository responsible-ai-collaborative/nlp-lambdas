import subprocess
import json
import ast
import argparse

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
    if (defaultShell):
        print(cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    else:
        print((['bash', '-c']+cmd))
        p = subprocess.Popen((['bash', '-c']+cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    
    stdout, err = p.communicate()

    # Wait for completion
    while p.poll() == None: continue
    bestID = None

    # Normal execution
    if (p.poll() == 0):
        print(f'Stdout: "{stdout}"')
        data = {}
        try:
            data = json.loads(json.loads(stdout))
        except:
            print('Failure in json parsing')

        try:
            if(data["statusCode"] == 200):
                listoftupals = ast.literal_eval(data['body']['msg'])
                bestID = listoftupals[0][1]
                print(f'bestID output: {bestID}')
        except:
            print('Error in reading SAM output')
    else:
        print(f'Error in SAM execution, exit code: {p.poll()}')

    return(expectIncident == bestID)

defaultShell = False

def main():
    # Use global defaultShell
    global defaultShell

    # Initialize parser
    parser = argparse.ArgumentParser()
    
    # Adding optional argument
    parser.add_argument("-i", "--ExpectIncidentNumber", type = int, help = "Give an Expect Incident Id number")
    parser.add_argument("-d", "--DocsJson", help = "Give a .\docs .json file path")
    parser.add_argument("--DefaultShell", action = "store_true", help = "Signal that you want to use your default shell rather than bash")
    
    # Read arguments from command line
    args = parser.parse_args()
    defaultShell = args.DefaultShell

    if args.ExpectIncidentNumber and args.DocsJson:
        return runTestPipeTest(args.ExpectIncidentNumber, args.DocsJson)
        # return runTest(args.ExpectIncidentNumber, args.DocsJson)

if __name__ == "__main__":
   main()
