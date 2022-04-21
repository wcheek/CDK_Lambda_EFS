from aws_cdk import Stack
from aws_cdk import aws_lambda as _lambda
from constructs import Construct


class CdkLambdaEfsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.lambda_func = None

        self.build_infrastructure()

    def build_infrastructure(self):
        self.build_lambda_func()

    def build_lambda_func(self):
        _lambda.Function(
            self,
            "LambdaWithEFS",
            runtime=_lambda.Runtime.PYTHON_3_9(),
            # lambda function file name.handler function
            handler="lambda_EFS.handler",
            # Points to directory of lambda function
            code=_lambda.Code.from_asset("cdk_lambda_efs/lambda_EFS"),
        )
