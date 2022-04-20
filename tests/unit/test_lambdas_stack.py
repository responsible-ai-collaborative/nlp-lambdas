import aws_cdk as core
import aws_cdk.assertions as assertions

from app import NlpLambdaStack

# example tests. To run these tests, uncomment this file along with the example
# resource in wow/wow_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = NlpLambdaStack(app, "AiidNlpStack")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
