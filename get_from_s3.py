#!/usr/bin/env python
import sys
import boto3
import numpy as np
from laspy.file import File

s3 = boto3.resource('s3')

obj = s3.Object('jippe-home', 'config.json')
print obj.get()['Body'].read()
