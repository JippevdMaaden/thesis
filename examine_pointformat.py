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

### Check for files in the folder
files_to_use = searchFiles(all_files, folder_var, file_var)
for file in files_to_use:

####### Initiate
	### Local variables to be used ###
	local_laz_file_name = 'local.laz'
	local_las_file_name = 'local.las'

	### Download file from S3 ###
	downloadFromS3(bucket_var, file, local_laz_file_name)

	### Convert LAZ to LAS ###
	convertLasZip(local_laz_file_name, local_las_file_name)

	### Remove LAZ file ###
	removeFile(local_laz_file_name)

####### Do something with the file

	
	inFile = openLasFile(local_las_file_name)
	
	#
  	print file
  	examinePointFormat(inFile)
	#
	
	closeLasFile(inFile)
	
####### Cleanup
	### Remove local file ###
	removeFile(local_las_file_name)
