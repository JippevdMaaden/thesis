#!/usr/bin/env python
import sys
import os
import boto3
import botocore
import numpy as np
import time
import random
import copy
import laspy

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

def minmax(val_list):
	min_val = min(val_list)
	max_val = max(val_list)

	return (min_val, max_val)

def explorePointLayout(lasfile):
	print 'Exploring lasfile layout'
	print

	print 'There are %s points in the LAS file' % (len(lasfile.Z))
	print
	print 'X values are ranged from %s-%s and look like this:' % (minmax(lasfile.X))
	print lasfile.X[:100]
	print

	print 'Y values are ranged from %s-%s and look like this:' % (minmax(lasfile.Y))
	print lasfile.Y[:100]
	print

	print 'Z values are ranged from %s-%s and look like this:' % (minmax(lasfile.Z))
	print lasfile.Z[:100]
	print

	print 'Intensity values are ranged from %s-%s and look like this:' % (minmax(lasfile.intensity))
	print lasfile.intensity[:100]
	print

	print 'Flag Byte holds multiple values which look like this:'
	print '    Return number values are ranged from %s-%s and look like this:' % (minmax(lasfile.return_num))
	print lasfile.return_num[:100]
	print
	print '    Number of Returns values are ranged from %s-%s and look like this:' % (minmax(lasfile.num_returns))
	print lasfile.num_returns[:100]
	print
	print '    Scan Direction Flag values are ranged from %s-%s and look like this:' % (minmax(lasfile.scan_dir_flag))
	print lasfile.scan_dir_flag[:100]
	print
	print '    Edge of Flight Line values are ranged from %s-%s and look like this:' % (minmax(lasfile.edge_flight_line))
	print lasfile.edge_flight_line[:100]
	print

	print 'Classification Byte holds multiple values which look like this:'
	print '    Classification values are ranged from %s-%s and look like this:' % (minmax(lasfile.classification))
	print lasfile.classification[:100]
	print
	print '    Synthetic values are ranged from %s-%s and look like this:' % (minmax(lasfile.synthetic))
	print lasfile.synthetic[:100]
	print
	print '    Key Point values are ranged from %s-%s and look like this:' % (minmax(lasfile.key_point))
	print lasfile.key_point[:100]
	print
	print '    Withheld values are ranged from %s-%s and look like this:' % (minmax(lasfile.withheld))
	print lasfile.withheld[:100]
	print


	print 'User Data values are ranged from %s-%s and look like this:' % (minmax(lasfile.user_data))
	print lasfile.user_data[:100]
	print

	print 'Scan Angle Rank values are ranged from %s-%s and look like this:' % (minmax(lasfile.scan_angle_rank))
	print lasfile.scan_angle_rank[:100]
	print

	print 'Point Source Id values are ranged from %s-%s and look like this:' % (minmax(lasfile.pt_src_id))
	print lasfile.pt_src_id[:100]
	print

	try:
		print 'GPS Time values are ranged from %s-5S and look like this:' & (minmax(lasfile.gps_time))
		print lasfile.gps_time[:100]
		print
	except:
		print 'No GPS Time in this LAS file'

	try:
		print 'Importance Value values are ranged from %s-%s and look like this:' % (minmax(lasfile.importance_value))
		print lasfile.importance_value[:100]
		print
	except AttributeError or util.laspyException:
		print 'No Importance Value in this LAS file'

def fillList(listSize, minRange, maxRange):
	inputList = []
	for i in range(0, listSize):
		el = random.randint(minRange, maxRange)
		inputList.append(el)
	return inputList

def version2to1(infile):
	new_header = copy.copy(infile.header)
	new_header.format = 1.2
	new_header.pt_dat_format_id = 1

	outFile = laspy.file.File("./output.las", mode = 'w', vlrs = infile.header.vlrs, header = new_header)


	for spec in inFile.reader.point_format:
		print("Copying dimension: " + spec.name)
		in_spec = infile.reader.get_dimension(spec.name)
		try:
			outFile.writer.set_dimension(spec.name, in_spec)
		except util.LaspyException:
			print "Couldn't set dimension: " + spec.name + " with file format " + str(outFile.header.version) + ", and point_format" + str(outFile.header.data_format_id)

	outFile.close()

def addI_currentfile(infile):
#	i_Values = fillList(len(lasfile.Z), 0, 999)
#	i_Values = random.sample(xrange(0,999), len(lasfile.Z))
#	i_Values = [random.choice(xrange(0,999)) for _ in range(len(lasfile.Z))]

	outfile = File('localI.las', mode = 'w', header = infile.header)

#	outfile.define_new_dimension(name = 'gps_time', data_type = 10, description = 'gps_time')

	for dimension in infile.point_format:
		dat = infile.reader.get_dimension(dimension.name)
		outfile.writer.set_dimension(dimension.name, dat)

	outfile.pt_src_id = [random.randint(0,15) for _ in range(len(outfile))]

#	outfile.importance_value = []

#	for i in range(len(outfile.X)):
#		outfile.importance_value.append(random.randomint(0,15))

	closeLasFile(outfile)

def addI_newfile(infile):
	print 'Generating Importance values'
	print

#	i_Values = fillList(len(lasfile.Z), 0, 999)
#	i_Values = random.sample(xrange(0,999), len(lasfile.Z))
#	i_Values = [random.choice(xrange(0,999)) for _ in range(len(lasfile.Z))]

#	outfile.define_new_dimension(name = 'importance_value', data_type = 6, description = 'Importance Value')

#	for dimension in infile.point_format:
#		dat = infile.reader.get_dimension(dimension.name)
#		outfile.writer.set_dimension(dimension.name, dat)

#	outfile.importance_value = []

#	for i in range(len(outfile.X)):
#		outfile.importance_value.append(random.randomint(0,15))

	extra_dimension_spec_1 = laspy.header.ExtraBytesStruct(name = 'My Super Special Dimension', data_type = 5)
	extra_dimension_spec_2 = laspy.header.ExtraBytesStruct(name = 'Another Special Dimension', data_type = 6)

	vlr_body = (extra_dimension_spec_1.to_byte_string() + extra_dimension_spec_2.to_byte_string())

	extra_dim_vlr = laspy.header.VLR(user_id = 'LASF_Spec', record_id = 4, description = 'Testing Extra Bytes.', VLR_body = vlr_body)

	new_header = copy.copy(infile.header)
	new_header.data_record_length += 8
	new_header.format = 1.4

	new_file = File('newfile.las', mode = 'w', header = new_header, vlrs = [extra_dim_vlr])

	for dimension in inFile.point_format:
		dim = infile._reader.get_dimension(dimension.name)
		new_file._writer.set_dimension(dimension.name, dim)

	new_file.my_super_special_dimension = [0]*len(new_file)
	new_file.another_special_dimension = [10]*len(new_file)

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

### Search all files in the bucket
all_files = searchInBucket(bucket_var)

### Check for files in the folder
files_to_use = searchFiles(all_files, folder_var, file_var)
for file in files_to_use:

### Local variables, should be user inputable
	local_laz_file_name = 'local.laz'
	local_las_file_name = 'local.las'
	new_bucket_name = 'jippe-tu-delft-campus-switch'


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

	examinePointFormat(inFile)
	examineHeader(inFile)
	explorePointLayout(inFile)

#	version2to1(inFile)

#	addI_newfile(inFile)
	addI_currentfile(inFile)

	closeLasFile(inFile)

	inFile = openLasFile('localI.las')

	examinePointFormat(inFile)
	examineHeader(inFile)
	explorePointLayout(inFile)

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

#print indexLasFile()
