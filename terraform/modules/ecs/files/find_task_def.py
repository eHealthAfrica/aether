#!/usr/bin/env python

import boto3
import json
import sys

client = boto3.client('ecs')

data = json.load(sys.stdin)
family_prefix = data['family_prefix']

task_def = client.list_task_definitions(familyPrefix=family_prefix,
                                        status="ACTIVE", sort="DESC", maxResults=1)

task_arn = task_def["taskDefinitionArns"]
sys.stdout.write(json.dumps({"task_arn": "%s" % task_arn[0]}))
sys.exit(0)
