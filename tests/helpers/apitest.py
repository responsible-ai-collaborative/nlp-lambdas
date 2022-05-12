import requests
import ast
import subprocess
import json
import argparse
import time
import sys
from custom_exceptions import (StartApiTimeoutException)
from loop_stopper import (LoopStopper)
from iterators import TimeoutIterator
import os
import signal
import psutil
import atexit

start_api_timeout = 60
request_timeout = 180
api_running = False
p_list = []

# Source: https://stackoverflow.com/a/25134985
def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

# Source: https://stackoverflow.com/a/320712
@atexit.register
def cleanup():
    global p_list
    global api_running
    timeout_sec = 1
    p_sec = 0
    for p in p_list:
        for second in range(timeout_sec):
            if p.poll() == None:
                time.sleep(1)
                p_sec += 1
        if p_sec >= timeout_sec and p:
            kill(p.pid)
            p.kill()
    p_list = []
    api_running = False

def api_full_test_run(expectIncident, docsJsonPath):
    # register global
    global p_list
    global api_running

    # start the api
    p = start_api()
    p_list.append(p)

    # initial, failing values
    res_get = -1
    res_post = -2

    # try to make test requests
    try:
        if api_running:
            # Open the provided json input and run a get and post request
            with open(docsJsonPath, encoding="utf-8") as json_file:
                res_get = run_get_test_fd(expectIncident, json_file)
                json_file.seek(0)
                res_post = run_post_test_fd(expectIncident, json_file)
    except Exception as e:
        api_running = False
        cleanup()
        raise e

    if p:
        kill(p.pid)
        out, err = p.communicate()
        api_running = False

    print(res_get)
    print(res_post)
    print(expectIncident)

    return(res_get == res_post == expectIncident)
    # return(res_get == expectIncident)

def start_api():
    global api_running
    global start_api_timeout

    if not api_running:
        # Run start-api command as subprocess
        cmd = ['sam', 'local', 'start-api', '-t', './cdk.out/AiidNlpLambdaStack.template.json']
        p = subprocess.Popen(' '.join(cmd), stderr=subprocess.PIPE, shell=True, universal_newlines=True)

        # Wait for api to be running
        it = TimeoutIterator(p.stderr, timeout=start_api_timeout)
        for line in it:
            print(line)
            if line == it.get_sentinel():
                kill(p.pid)
                out, err = p.communicate()
                it.interrupt()
                raise StartApiTimeoutException
            elif "(Press CTRL+C to quit)" in str(line):
                it.interrupt()
                break
        
        api_running = True
        return p

    return None

def run_get_test_path(expectIncident, docsJsonPath):
    with open(docsJsonPath, encoding="utf-8") as json_file:
        return run_get_test_fd(expectIncident, json_file)

    return False

def run_get_test_fd(expectIncident, json_file):
    json_payload = json.load(json_file)
    get_payload = json_payload['text']
    get_url = ('http://127.0.0.1:3000/similar?text=\\"' + get_payload + '\\"')
    print("before request")
    res = requests.get(get_url, timeout=request_timeout)
    print(f"after request, res = {res}")
    print(res.json())
    getOutputIncident = ast.literal_eval(json.loads(res.text)['body']['msg'])[0][1]
    print(getOutputIncident)

    return (getOutputIncident == expectIncident)

def run_post_test_path(expectIncident, docsJsonPath):
    with open(docsJsonPath, encoding="utf-8") as json_file:
        return run_post_test_fd(expectIncident, json_file)

    return False

def run_post_test_fd(expectIncident, json_file):
    json_payload = json.load(json_file)
    # print(f"req: {json_payload}")
    res = requests.post("http://127.0.0.1:3000/similar", json=json_payload, timeout=request_timeout)
    print(f"res = {res}")
    print(res.json())
    postOutputIncident = ast.literal_eval(json.loads(res.text)['body']['msg'])[0][1]
    print(postOutputIncident)

    return(postOutputIncident == expectIncident)

def main():
     # Initialize parser
    parser = argparse.ArgumentParser()
    
    # Adding optional argument
    parser.add_argument("-i", "--ExpectIncidentNumber", type = int, required = True, help = "Give an Expect Incident Id number")
    parser.add_argument("-d", "--DocsJson", required = True, help = "Give a ./docs .json file path")
    
    # Read arguments from command lineW
    args = parser.parse_args()

    if args.ExpectIncidentNumber and args.DocsJson:
        sys.exit(not api_full_test_run(args.ExpectIncidentNumber, args.DocsJson))


if __name__ == "__main__":
    main()