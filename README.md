# service
A quick python library for playing with services in Linux

## Usage Example

**AWS Service Alerting**

Simple demo that checks if a list of services are running and alerts an SNS topic.

```
import boto3
import subprocess
import service

# Create an SNS client
client = boto3.client(
    "sns",
    aws_access_key_id="",
    aws_secret_access_key="",
    region_name=""
)

topic_arn = ""
services = ['mongod','nginx','php5.6-fpm']
message = ""

for x in services:
    print("Checking Process: {}".format(x))
    if not service.running(x):
        message=message + "{} NOT RUNNING!\n".format(x)

if message != "":
    client.publish(Message=message, TopicArn=topic_arn, Subject='ALERT: Process monitor failing')
```
