#!/usr/bin/env python

import boto3
import botocore

from util.utils import *

### Create connection to s3
client = boto3.client('s3')
resource = boto3.resource('s3')

### Get bucket, folder and file variable
bucket_var = raw_input('What bucket do you want to search?\n')
folder_var = raw_input('What folder do you want to search?\n')
file_var = raw_input('What file do you want to search?\n')
print

### Search all files in the bucket
all_files = searchInBucket(bucket_var)

### Get amount of threads
threads_var = raw_input('How many threads should Entwine use?\n')
print

### Get schema
schema_bool = raw_input('Should Entwine use a schema? (y/n)\n')
print
schema_var = ''
if schema_bool == 'y':
  schema_var = raw_input('Which schema should Entwine use?\n')
  print

i = 's3://' + bucket_var + '/'
if folder_var != '':
  i += folder_var + '/'
  if file_var != '':
    i += file_var
    
o = 's3://jippe-test/greyhound/' + bucket_var

t = threads_var

s = 's3://jippe-home/' + schema_var

runstring = 'docker run -it -v ~/.aws:/root/.aws connormanning/entwine build' + ' -i ' + i + ' -o ' + o + ' -t ' + t

if schema_bool == 'y':
  runstring = 'docker run -it -v ~/.aws:/root/.aws connormanning/entwine build' + ' ' + s
  
print runstring
#os.system(runstring)
