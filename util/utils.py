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

### Create connection to s3
client = boto3.client('s3')
resource = boto3.resource('s3')

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
			raise #raise custom error here

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

def examinePointFormat(inFile):
	print 'Examining Point Format: '
	print

	pointformat = inFile.point_format
  
	for spec in pointformat:
		print(spec.name)
	print

def examineHeader(inFile):
	print 'Examining Header: '
	print

	headerformat = inFile.header.header_format
  
	for spec in headerformat:
		name = spec.name
    
		try:
			print '%s: %s' % (name, getattr(inFile.header,name))
		except AttributeError:
			pass
	print

def swapLasValues(inFile, value1, value2):
	print 'Swapping %s and %s values' % (str(value1), str(value2)) # make proper dimension.name
	print

	A = inFile.value1
	B = inFile.value2
	inFile.value1 = B
	inFile.value2 = A

def minmax(val_list):
	min_val = min(val_list)
	max_val = max(val_list)

	return (min_val, max_val)

def explorePointLayout(inFile):
	print 'Exploring lasfile layout'
	print

  	print 'There are %s points in the LAS file' % getattr(inFile.header, 'point_records_count')
	print
  
	pointformat = inFile.point_format
  
	for spec in pointformat:
		name = spec.name
		attribute = getattr(inFile, name)
    		print '%s values are ranged from %s-%s and look like this' % (name, minmax(attribute)[0], minmax(attribute)[1])
    		print attribute
    		print
   
def exploreSubBytePointLayout(inFile):
# Add flag byte (return_num, num_returns, scan_dir_flag and edge_flight_line)
# Add classification byte (classification, synthetic, key_point, withheld)
	pass

def fillList(listSize, minRange, maxRange):
  
	inputList = []
  
	for i in range(0, listSize):
		el = random.randint(minRange, maxRange)
		inputList.append(el)
    
	return inputList

def changeLASversion(lasfile, newlasversion, newpointversion): # output name should be param?
	print 'Changing point format of %s to %s' % (lasfile, newpointversion)
	print
	
	variable = 'las2las -i %s -o outfile.las -remove_vlrs_from_to 1 3 -remove_padding -set_version %s -set_point_type %s -cores 1' % (lasfile, newlasversion, newpointversion)
	
	os.system(variable)

def addI_currentfile(inFile):
  	print 'Generating Importance value for %s' % str(inFile)
  
	outFile = File('localI.las', mode = 'w', header = inFile.header)

	outFile.define_new_dimension(name = 'gps_time', data_type = 10, description = 'gps_time')

	for dimension in inFile.point_format:
		dat = inFile.reader.get_dimension(dimension.name)
		outFile.writer.set_dimension(dimension.name, dat)

	outFile.pt_src_id = [random.randint(0,15) for _ in range(len(outFile))]

	outFile.gps_time = []

	for i in range(len(outFile.X)):
		outFile.importance_value.append(random.randomint(0,15))

	closeLasFile(outFile)
  
  	return "localI.las"

def addGPSTime_currentfile(inFile):
	print 'Adding GPS Time to %s' % str(inFile)
	
	inFile.gps_time = fillList(getattr(inFile.header, 'point_records_count'), 0, 999)

def closeLasFile(lasfile):
	print 'Closing %s' % str(lasfile)
	print

	lasfile.close()

def indexLasFile(s):
	print 'Indexing using Entwine with %s.json' % (s)
	print

	schema = 's3://jippe-home/%s.json' % s

	variable = 'docker run -it -v ~/.aws:/root/.aws connormanning/entwine build -i %s' % schema

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

def listBuckets():
  	s3 = boto3.resource('s3')
  
  	for bucket in s3.buckets.all():
    		print bucket.name
    		print "---"
		
    		for item in bucket.objects.all():
      			print "\t%s, (%s MB)" % (item.key, item.size/1000000)
    		
		print
  
def sortbyGPSTime(inputfile, outputfile, gps_time = False):
	if gps_time == True:
		print 'Sorting %s by gps_time'
		print
		
		variable = 'lassort -i %s -o %s -gps_time' % (inputfile, outputfile)
		
		os.system(variable)
	
	else:
		print 'Sorting %s'
		print
		
		variable == 'lassort -i %s -o %s' % (inputfile, outputfile)
		
		os.system(variable)
		
def fillRandomVariable(inFile, variable):
	version = getattr(inFile.header, 'version_minor')
	sizedict = lasPointFormat()
	
	numbytes = sizedict[version][variable]
	
	minRange = 0
	#maxRange = (2 ** (numbytes * 8)) - 1
	maxRange = 15
		
	inputlist = fillList(getattr(inFile.header, 'point_records_count'), minRange, maxRange)
	
	inFile.intensity = inputlist
	
def lasPointFormat():
	formatdict = {}
	
	formatdict[0] = {}
	formatdict[1] = {}
	formatdict[2] = {}
	
	for key in formatdict:
		formatdict[key]['intensity'] = 2
	
	return formatdict

def normalize(vector):
	lengthv = (vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2) ** 0.5
	nvector = [vector[0] / lengthv, vector[1] / lengthv, vector[2] / lengthv]
	return nvector

class CameraCone:
	# use local ref system (translation matrix) or global ref system? Currently global hardcoded for tu-delft-campus top down
	def __init__(self, origin, lens, fov):
		# translation matrix for camera relative to env (crs)
		#self.matrix = matrix.inverted()
		self.origin = [85910, 445600, 2000]
		target = [85910, 445600, -1000]
		self.lens = [target[0] - origin[0], target[1] - origin[1], target[2] - origin[2]]

		# translation matrix testing
		
		#move the camera 500 to the right (x?)
		viewmatrix = np.matrix([[1,0,0,50],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
		self.translationmatrix = viewmatrix.I
		
		
		# adjust for possible rectangular resolution
		
		#w = 0.5 * sensor_width / lens
		#if resolution_x > resolution_y:
		#    x = w
		#    y = w * resolution_y / resolution_x
		#else:
		#    x = w * resolution_x / resolution_y
		#    y = w

		#lr = [x, -y, -1]
		#ur = [x, y, -1]
		#ll = [-x, -y, -1]
		#ul = [-x, y, -1]

		lr = [5000, -5000, -1000]
		ur = [5000, 5000, -1000]
		ll = [-5000, -5000, -1000]
		ul = [-5000, 5000, -1000]

		# normalize normals
		self.half_plane_normals = [
		    normalize(np.cross(lr, ll)),
		    normalize(np.cross(ll, ul)),
		    normalize(np.cross(ul, ur)),
		    normalize(np.cross(ur, lr))
		]

    	def isVisible(self, point, fudge = 0):
		# translation to local camera CRS
		#loc2 = self.matrix * loc

		#for norm in self.half_plane_normals:
		    #z2 = loc2.dor(norm)
		    #if z2 < -fudge:
			#return False

		#return True

		#adjust point because of hardcode

		temppoint = [point[0] - 85910, point[1] - 445600, -point[2], 1]
		temppoint2 = self.translationmatrix.dot(temppoint)
		temppoint3 = temppoint2.tolist()
		temppoint4 = temppoint3[0]
		pointv = [temppoint4[0], temppoint4[1], temppoint4[2]]

		#positive?
		#pointv = [point[0] - self.origin[0], point[1] - self.origin[1], point[2] - self.origin[2]]
		#or
		#negative?
		#poitnv = [self.origin[0] - point[0], self.origin[1] - point[1], self.origin[2] - point[2]]

		for norm in self.half_plane_normals:
			z = np.dot(pointv, norm)
			if z < -fudge:
				return False

		return True
