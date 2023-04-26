import * as cdk from 'aws-cdk-lib';
import { LambdaRestApi } from 'aws-cdk-lib/aws-apigateway';
import { Code, Function, Runtime } from 'aws-cdk-lib/aws-lambda';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
import * as path from "path";
// import * as sqs from 'aws-cdk-lib/aws-sqs';

export class GeneratorStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const bucket = new Bucket(this, "GeneratorBucket", {
      bucketName: "uvic-schedule-generator-bucket",
      versioned: true,
    });

    const handler = new Function(this, 'GeneratorFunction', {
      code: Code.fromAsset(path.join(__dirname, "../app")),
      handler: "insert entrypoint here",
      runtime: Runtime.JAVA_11,
    });

    const api = new LambdaRestApi(this, 'GeneratorAPI', {
      handler,
    });
  }
}
