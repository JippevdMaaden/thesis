#!/usr/bin/env python
import sys
from awscli.customizations.s3.utils import split_s3_bucket_key
import boto3
import numpy as np
from laspy.file import File
import time

client = boto3.client('s3')
resource = boto3.resource('s3')

var = raw_input('What bucket and file do you want to search?\n')
bucket_name, key_name = split_s3_bucket_key(var)

print 'Searching %s' % bucket_name
print
print '%s contains the following files:' % bucket_name
print

for item in resource.Bucket(bucket_name).objects.all():
	print '\t%s, (%s MB)' % (item.key, item.size / 1000000)

print
print 'Found %s' % key_name
print 

time.sleep(1)

response = client.get_object(Bucket=bucket_name, Key=key_name)

print 'File header:'
print response
print
