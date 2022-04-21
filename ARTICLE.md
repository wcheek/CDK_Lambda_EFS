# Lambda function with persistent file store using AWS CDK and AWS EFS

Have you ever wanted Lambda functions to be able to save and load files locally without needing to transfer data between an S3 bucket? This article is for you.

By using `AWS EFS` we can [attach a persistent filesystem](https://aws.amazon.com/blogs/compute/using-amazon-efs-for-aws-lambda-in-your-serverless-applications/) to your Lambda function!

[GitHub Repository](https://github.com/wcheek/CDK_Lambda_EFS)

## CDK init & deploy

I won’t cover setting up CDK and bootstrapping the environment. You can find that information [here.](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)

Once you have set up CDK, we need to set up the project:

1. `mkdir cdk_docker_lambda && cd cdk_docker_lambda`

2. `cdk init --language python`

3. `source .venv/bin/activate`

4. `pip install -r requirements.txt && pip install -r requirements-dev.txt`

    Now deploy empty stack to AWS:

5. `cdk deploy`

## Stack design

Our CDK stack is going to deploy an `EFS` filesystem, a Lambda function, and an access point which will allow us to attach the filesystem to the function.

### cdk_lambda_efs/cdk_lambda_efs_stack.py

```python
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
            file_system_name="ExampleLambdaAttachedEFS",
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
        # I'm just using the normal CDK lambda function here. See my other articles for additional building methods.
        _lambda.Function(
            self,
            "LambdaWithEFS",
            runtime=_lambda.Runtime.PYTHON_3_9,
            # lambda function file name.handler function
            handler="lambda_EFS.handler",
            # Points to directory of lambda function
            code=_lambda.Code.from_asset("cdk_lambda_efs/lambda_EFS"),
            # Lambda needs to be in same VPC as EFS
            vpc=self.vpc,
            filesystem=_lambda.FileSystem.from_efs_access_point(
                ap=self.access_point, mount_path="/mnt/filesystem"
            ) if self.access_point else None,
        )

```

## Lambda function

I will deploy a lambda function without any additional dependencies. If you need dependencies, you will need to use different `CDK` constructs to do it. [Here is an example of using aws_lambda_python_alpha](https://dev.to/wesleycheek/deploy-an-api-fronted-lambda-function-using-aws-cdk-2nch) and [here is an example of building using Docker](https://dev.to/wesleycheek/deploy-a-docker-built-lambda-function-with-aws-cdk-fio).

This lambda function opens a file on the `EFS` filesystem, writes a string to it, then opens it again and returns the result.

### cdk_lambda_efs/lambda_EFS/lambda_EFS.py

```python
from pathlib import Path


def handler(event, context):
    # Writing to a file on the EFS filesystem
    path = Path("/mnt/filesystem/test.txt")
    with path.open("w") as f:
        f.write("Test123")
    # Now open the file, read the text, return
    with path.open("r") as f:
        text = f.read()
    return f"Hello Lambda! {text}"

```

## Test the lambda function with attached filesystem

Navigate to the Lambda console on AWS. First notice the filesystem has been successfully attached to your lambda function

![attached_filesystem](D:\Projects\Notes\My Articles\4_CDK_Lambda_EFS\Assets\attached_filesystem.png)

Now go ahead and test it using any kind of event.

![image-20220421130248278](D:\Projects\Notes\My Articles\4_CDK_Lambda_EFS\Assets\image-20220421130248278.png)

I hope this article has helped you to solve your problem of lambda not persisting data. EFS is an easy to use and versatile solution to memory problems.
