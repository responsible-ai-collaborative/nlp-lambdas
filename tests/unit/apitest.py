import requests
import ast
import subprocess
import json
import time

# start the api
cmd = ['sam', 'local', 'start-api', '-t', '.\cdk.out\AiidNlpLambdaStack.template.json']

with open("stdout.json","wb") as out, open("stderr.txt","wb") as err:
    p = subprocess.Popen(cmd,stdout=out,stderr=err, shell=True)
    time.sleep(10)

    res = requests.get("http://127.0.0.1:3000/similar?text=\"wow\"")
    print(ast.literal_eval(json.loads(res.text)['body']['msg'])[0][1])

    res = requests.post("http://127.0.0.1:3000/similar", json={"text":"wow", "num":"3"})
    print(ast.literal_eval(json.loads(res.text)['body']['msg'])[0][1])
    p.kill()