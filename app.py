import aws_cdk as cdk

from cdk_lambda_efs.cdk_lambda_efs_stack import CdkLambdaEfsStack

app = cdk.App()
CdkLambdaEfsStack(
    app,
    "CdkLambdaEfsStack",
)

app.synth()
