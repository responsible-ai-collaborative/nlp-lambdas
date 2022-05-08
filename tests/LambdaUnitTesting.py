import unittest
import testrun
import time
import subprocess
import json
import ast


def test1():
    assert testrun.runTestPipeTest(1, "..\doc\example_invoke_long.json") == True
    # assert runTestPipeTest(1, "..\doc\example_invoke_long.json") == True

def test2():
    assert testrun.runTestPipeTest(15, "..\doc\\example_test_data_15.json") == True
    # assert runTestPipeTest(15, "..\doc\\text15.json") == True


# def runTestPipeTest(expectIncident, docsJsonPath):
#     # Define command for subprocess
#     cmd = ['sam', 'local', 'invoke', 'similar', '-t', './cdk.out/AiidNlpLambdaStack.template.json', '-e', docsJsonPath]

#     # Spawn subprocess and wait for its complete stdout (depending on DefaultShell argument)
#     print(cmd)
#     p = subprocess.Popen(' '.join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
#     stdout, err = p.communicate()

#     print(f'stdout: "{json.loads(stdout)}"')
#     print(f'stderr: "{err}"')

#     # Wait for completion
#     while p.poll() == None: continue
#     bestID = None

#     # Normal execution
#     if (p.poll() == 0):
#         data = {}
#         try:
#             data = json.loads(json.loads(stdout))
#         except:
#             raise Exception('Failure in json parsing')

#         try:
#             if(data["statusCode"] == 200):
#                 listoftupals = ast.literal_eval(data['body']['msg'])
#                 bestID = listoftupals[0][1]
#                 print(f'bestID output: {bestID}')
#         except:
#             raise Exception('Error in reading SAM output, stderr: "{err}"')
#     else:
#         raise Exception(f'Error in SAM execution, exit code: {p.poll()}')

    # return(expectIncident == bestID)