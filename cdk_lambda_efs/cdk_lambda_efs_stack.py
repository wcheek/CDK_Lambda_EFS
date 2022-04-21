from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_efs as efs
from aws_cdk import aws_lambda as _lambda
from constructs import Construct
from aws_cdk import RemovalPolicy


class CdkLambdaEfsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # I like to define all my pieces in __init__
        self.vpc = None
        self.access_point = None
        self.lambda_func = None

        self.build_infrastructure()

    def build_infrastructure(self):
        self.build_vpc()
        self.build_filesystem()
        self.build_lambda_func()

    def build_vpc(self):
        # Build the VPC where both EFS and Lambda will sit
        self.vpc = ec2.Vpc(self, "VPC")

    def build_filesystem(self):
        file_system = efs.FileSystem(
            scope=self,
            id="Efs",
            vpc=self.vpc,
            file_system_name="DryerPredictionsEFS",
            # Makes sure to delete EFS when stack goes down
            removal_policy=RemovalPolicy.DESTROY,
        )
        # create a new access point from the filesystem
        self.access_point = file_system.add_access_point(
            "AccessPoint",
            # set /export/lambda as the root of the access point
            path="/export/lambda",
            # as /export/lambda does not exist in a new efs filesystem, the efs will create the directory with the following createAcl
            create_acl=efs.Acl(
                owner_uid="1001", owner_gid="1001", permissions="750"
            ),
            # enforce the POSIX identity so lambda function will access with this identity
            posix_user=efs.PosixUser(uid="1001", gid="1001"),
        )

    def build_lambda_func(self):
        _lambda.Function(
            self,
            "LambdaWithEFS",
            runtime=_lambda.Runtime.PYTHON_3_9(),
            # lambda function file name.handler function
            handler="lambda_EFS.handler",
            # Points to directory of lambda function
            code=_lambda.Code.from_asset("cdk_lambda_efs/lambda_EFS"),
            # Lambda needs to be in same VPC as EFS
            vpc=self.vpc,
            filesystem=_lambda.FileSystem.from_efs_access_point(
                ap=self.access_point, mount_path="/mnt/models"
            ) if self.access_point else None,
        )
