#!/usr/bin/env python
import sys
import os
import boto3
import botocore
import numpy as np
import time

from awscli.customizations.s3.utils import split_s3_bucket_key
from laspy.file import File
from io import BytesIO

###################################################################################################################
def searchInBucket(bucketname):
	print 'Searching all files in %s' % bucketname
	print
	bucketContent = []
	try:
		for item in resource.Bucket(bucketname).objects.all():
			bucketContent.append(item.key)
	except botocore.exceptions.ClientError:
		print 'This bucket is not available'
		quit()
	return bucketContent

def downloadFromS3(bucketname, filename, newfilename):
	print 'Downloading %s from s3 as %s' % (filename, newfilename)
	print

	try:
		resource.Bucket(bucketname).download_file(filename, newfilename)
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			print 'The object does not exist.'
		else:
			raise

def convertLasZip(input, output):
	print 'Converting %s to %s' % (input, output)
	print

	converting_laz_las = 'laszip -i %s -o %s' % (input, output)
	os.system(converting_laz_las)

def removeFile(filename):
	print 'Removing %s' % filename
	print

	os.remove(filename)

def uploadToS3(localfilename, bucketname, uploadfilename):
	print 'Uploading %s to %s as %s' % (localfilename, bucketname, uploadfilename)
	print

	client.upload_file(localfilename, bucketname, uploadfilename)

def openLasFile(lasfile):
	print 'Opening %s' % lasfile
	print
	return File(lasfile, mode = 'rw')

def examinePointFormat(lasfile):
	print 'Examining Point Format: '
	print

	pointformat = lasfile.point_format
	for spec in pointformat:
		print(spec.name)
	print

def examineHeader(lasfile):
	print 'Examining Header: '
	print

	headerformat = lasfile.header.header_format
	for spec in headerformat:
		name = spec.name
		try:
			print '%s: %s' % (name, getattr(lasfile.header,name))
		except AttributeError:
			pass
	print

def swapYandZ(lasfile):
	print 'Swapping Y and Z values'
	print

	Z = lasfile.Z
	Y = lasfile.Y
	lasfile.Y = Z
	lasfile.Z = Y

def closeLasFile(lasfile):
	print 'Closing the file...'
	print

	lasfile.close()

def indexLasFile():
	print 'Indexing with Entwine'
	print

	s = 's3://jippe-home/schema.json'
	i = 's3://jippe-deep-test/TU_Delft_Campus_Tiles'
	o = 's3://jippe-test/greyhound/tu-delft-campus-automated'

	variable = 'docker run -it -v ~/.aws:/root/.aws connormanning/entwine build -i %s -o %s' % (i, o)
	return variable
	os.system(variable)

def searchFiles(bucketfiles, folder, file):
	filesToUse = []
	for bucketfile in bucketfiles:
		if folder != '':
			if bucketfile[:len(folder)] == folder and bucketfile not in filesToUse:
				filesToUse.append(bucketfile)
		if file != '':
			if bucketfile[-len(file):] == file and bucketfile not in filesToUse:
				filesToUse.append(bucketfile)
	if not filesToUse:
		print 'This bucket contains nothing of interest'
	return filesToUse

###################################################################################################################

### Create connection to s3
client = boto3.client('s3')
resource = boto3.resource('s3')

### Which bucket and file? --- Format should be s3 url
#var = raw_input('What bucket and file do you want to search?\n')
#print

#bucket_name, key_name = split_s3_bucket_key(var)

### Get bucket, folder and file variable
bucket_var = raw_input('What bucket do you want to search?\n')
folder_var = raw_input('What folder do you want to search?\n')
file_var = raw_input('What file do you want to search?\n')
print

### Local variables, should be user inputable
local_laz_file_name = 'local.laz'
local_las_file_name = 'local.las'
new_bucket_name = 'jippe-deep-test'

### Search all files in the bucket
all_files = searchInBucket(bucket_var)

### Check for files in the folder
files_to_use = searchFiles(all_files, folder_var, file_var)
for file in files_to_use:

	### Download file from S3 ###
	downloadFromS3(bucket_var, file, local_laz_file_name)

	### Convert LAZ to LAS ###
	convertLasZip(local_laz_file_name, local_las_file_name)

	### Remove LAZ file ###
	removeFile(local_laz_file_name)

	###
	### Do something with the file
	###
	inFile = openLasFile(local_las_file_name)

	#examinePointFormat(inFile)
	#examineHeader(inFile)
	swapYandZ(inFile)

	closeLasFile(inFile)
	###
	###
	###

	### Convert LAS to LAZ ###
	convertLasZip(local_las_file_name, local_laz_file_name)

	### Upload file to S3 ###
	uploadToS3(local_laz_file_name, new_bucket_name, file)

	### Remove local file ###
	removeFile(local_las_file_name)
	removeFile(local_laz_file_name)

print indexLasFile()
