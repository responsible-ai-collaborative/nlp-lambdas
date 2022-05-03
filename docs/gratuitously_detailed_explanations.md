# Gratuitously Detailed Explanations


## Lambda Definition Scripts (```similar.py```)
The CDK app generates a Lambda function backed by a container image and a Python inference script, for each Python script in the inference directory. For example, the ```similar.py``` script shows how to use a local model file contained in the Docker conatainer (note the ```local_files_only``` option usage) and handle event input and output w/ the AWS Lambda<->API Proxy-Integration:
```python
# Paraphrased for simplicity (esp. no error handling)
import os
import json
import torch
from transformers import LongformerTokenizer, LongformerModel
from unidecode import unidecode

# Load NLP models and state from files in container and store
#    global vars in EFS cache for faster subsequent execution
model = LongformerModel.from_pretrained('/function/model',
                                        local_files_only=True)
tokenizer = LongformerTokenizer.from_pretrained('/function/model',
                                                local_files_only=True)
tensors = torch.load('/function/model/incident_cls.pt')

def process(text, tensors):
    inp = tokenizer(text, padding="longest",
                    truncation="longest_first",
                    return_tensors="pt")
    out = model(**inp)
    similarities = [
        torch.nn.functional.cosine_similarity(out.last_hidden_state[0][0],
                                              tensors[i].mean(0), 
                                              dim=-1
                                             ).item()
        if tensors[i] != None else torch.zeros(1)
        for i in range(len(tensors))
    ]
    return [j for j in sorted(zip(similarities, range(1, len(tensors) + 1)), reverse=True)]

def handler(event, context):
    result = {
        "isBase64Encoded": False,
        "statusCode": 500,
        "headers": { "Content-Type": "application/json" },
        "multiValueHeaders": { },
        "body": ""
    }
    
    event_text = json.loads(event['body'])['text'] # for post requests
    event_text = unidecode(event_text) # handle unicode input
    
    result['body']['msg'] = str(process(event_text, best_of))
    result['statusCode'] = 200
    
    return json.dumps(result)
```


## Longformer Model
When a call is made to the API, the input text is tokenized and processed by the Longformer Model. The output is a tensor representation. The Special Classification (CLS) token is the first vector in this processed representation, and contains some latent information about the input text.

The CLS vector is then compared, using cosine similarity, to the current stored state for each incident in the Incident Database. The incident state is the mean of the preprocessed CLS tokens of all reports for that incident. Updating this state will later be done automatically via GitHub Actions, either when reports are added to the Incident Database, or on a regular basis, e.g. once per day.

The output of the comparison is a list of confidence scores, describing the input text's similarity to each incident. The highest N of these are the most similar incidents to the input text, and are sent as the response to the API call.

## CDK Script
The CDK script is named ```app.py``` in the solution's repository. This script describes the AWS stack for the Lambda solution using the CDK V2 python library, to enable the CDK CLI application to facillitate deployment to AWS servers. The important segments of this script are described below:

The beginning of the script (global scope) imports the necessary libraries, allows the use of ```.env``` environment variables, and establishes the AWS account and region to be used for the stack:
```python
import os;
from dotenv import load_dotenv
from pathlib import Path
from aws_cdk import (
    aws_lambda as lambda_,
    aws_apigatewayv2_alpha as api_gw2_a, # apigatewayv2 is in alpha stage
    aws_efs as efs,
    aws_ec2 as ec2
)
from aws_cdk import (App, Stack, Duration, RemovalPolicy,
                     Environment, CfnCondition, Fn, CfnOutput)
from aws_cdk.aws_apigatewayv2_integrations_alpha import HttpLambdaIntegration # apigatewayv2 is in alpha stage
from constructs import Construct

load_dotenv()
aws_env = Environment(account=os.environ['AWS_ACCOUNT_ID'],
                      region=os.environ['AWS_REGION'])
```

The remainder of the script is contaiend within the ```__init__``` method of the ```ServerlessHuggingFaceStack``` AWS stack:
```python
# Stack for this cdk program
class ServerlessHuggingFaceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        ...
```

The beginning of this stack description creates a virtual private cloud (VPC) that is necessary for the housing the EFS for caching. The current version of this solution intentionally uses an [Internet Gateway]() rather than a [NAT Gateway](). This means that there is no internet access within the lambda execution like there would be with a NAT Gateway, but also reduces cost of hosting from $2 a day (at time of writing) to $0.01 a day. The following code examples shows how to do each of these:
- **Recommended** VPC with no NAT Gateway (using Fargate Internet Gateway with public subnet):
    ```python
    # Virtual private cloud with no NAT Gateway (Fargate Internet Gateway with public subnet):
    vpc = ec2.Vpc(self, 'FargateVPC',
                  cidr='10.0.0.0/16',
                  max_azs=1,
                  nat_gateways=0,
                  subnet_configuration=[
                      {'cidr_mask': 24,
                       'name': 'Public',
                       'subnetType': ec2.SubnetType.PUBLIC }
                  ])
    ``` 
- **OR** VPC w/ the default NAT Gateway (and private subnet, **extra costs**):
    ```python
    # **OR** Virtual private cloud with the default NAT Gateway (and private subnet):
    vpc = ec2.Vpc(self, 'Vpc', max_azs=2)
    ```
    
Next, the CDK script creates the EFS file system and an access point in EFS for the cached model:
```python
# Create a file system in EFS to store cache models
fs = efs.FileSystem(self, 'FileSystem',
                    vpc=vpc,
                    removal_policy=RemovalPolicy.DESTROY)
access_point = fs.add_access_point('MLAccessPoint',
                                   create_acl=efs.Acl(
                                       owner_gid='1001', owner_uid='1001', permissions='750'
                                   ),
                                   path="/export/models",
                                   posix_user=efs.PosixUser(gid="1001", uid="1001"))
```

Next, the CDK script creates the Http API Gateway for this stack (the lambda integrations and routes on this API are added later):
```python
# Create Http Gateway API for this stack
methods = [api_gw2_a.CorsHttpMethod.GET,
           api_gw2_a.CorsHttpMethod.POST]
httpApi = api_gw2_a.HttpApi(self, 'HttpApi',
                            description='HTTP API Gateway for AIID Lambdas',
                            cors_preflight={
                              'allow_headers': ['Content-Type',
                                               'X-Amz-Date',
                                               'Authorization',
                                               'X-Api-Key', ],
                              'allow_methods': methods,
                              'allow_credentials': True,
                              'allow_origins': ['http://localhost:3000'],
                            }
                           )

# Create a CDK output for the api url
# this outputs the apiUrl to a json file when deploying the stack, so it can be used by other programs as needed
CfnOutput(self, 'apiUrl', value=httpApi.url)
```

It then iterates through the Python files in the inference directory:
```python
docker_folder = os.path.dirname(
    os.path.realpath(__file__)) + "/inference"
pathlist = Path(docker_folder).rglob('*.py')
for path in pathlist
    ...
```

And for each lambda ```.py``` file found, it creates a Lambda function that serves the inference requests and adds this lambda as a route on the API with a Lambda Proxy Integration:
```python
# Parse lambda handler filename name
base = os.path.basename(path)
filename = os.path.splitext(base)[0]

# Lambda Function from docker image
function = lambda_.DockerImageFunction(
    self, filename,
    allow_public_subnet=True, # important for Internet Gateway
    code=lambda_.DockerImageCode.from_image_asset(
        docker_folder, cmd=[filename+".handler"]),
    memory_size=8096,
    timeout=Duration.seconds(600),
    vpc=vpc,
    filesystem=lambda_.FileSystem.from_efs_access_point(
        access_point, '/mnt/hf_models_cache'), # Establish cache
    environment={ # example environment variables that you could use in the lambda scripts after being set here
        "TRANSFORMERS_CACHE": "/mnt/hf_models_cache",
        "MODEL_DIR": "model",
        "MODEL_FILENAME": "pytorch_model.bin",
        "INCIDENTS_FILENAME": "incident_cls.pt",
        "CSV_FILENAME": "incidents.csv",
        "HF_MODEL_URI": "allenai/longformer-base-4096"
    },
)

# Create lambda integration for use in the Gateway API
lambda_integration = HttpLambdaIntegration('LambdaIntegration', function)

# Add route lambda integration to a route on the api, using the fn 
#     name and allowing for both GET and POST requests to this lambda
httpApi.add_routes(
    path=f"/{filename}",
    methods=[api_gw2_a.HttpMethod.GET, api_gw2_a.HttpMethod.POST],
    integration=lambda_integration
)
```

After the Stack is defined, back at the global scope, the CDK script concludes by initializing the AWS stack:
```python
# Initialize the aws stack
app = App()
ServerlessHuggingFaceStack(app,
                           "ServerlessHuggingFaceStack",
                           env=aws_env)
app.synth()
```
