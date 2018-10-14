
import urllib3
import numpy as np
import json
import struct
import laspy
import sys
import scipy.spatial
import time
import urlparse
import click

from laspy.file import File

sys.path.insert(0, '/home/ec2-user/thesis')

from util.utils import *

#
# This file will test the vario_scale_1.py method for
# the SPECKLY request when the file tu-delft-campus is loaded
# url = http://speck.ly/?s=ec2-54-93-124-194.eu-central-1.compute.amazonaws.com%3A8080%2F&r=tu-delft-campus&ca=0&ce=40&ct=85900.705%2C445593.72%2C45.170&cd=1362.928&cmd=5451.713&ps=2&pa=0.1&ze=1&c0s=remote%3A%2F%2Fimagery%3Furl%3Dhttp%253A%252F%252Fapi.tiles.mapbox.com%252Fv4%252Fmapbox.satellite%252F%257B%257Bz%257D%257D%252F%257B%257Bx%257D%257D%252F%257B%257By%257D%257D.jpg70%253Faccess_token%253Dpk.eyJ1IjoiaG9idSIsImEiOiItRUhHLW9NIn0.RJvshvzdstRBtmuzSzmLZw
# 
# The camera parameters are known from the url, but should now
# still be manually entered
#
# The implemented method uses automatic processing as described
# during my P3 presentation
#
# This file adds all the densities together afther the basics
# then it combines all point cloud files and filteres the
# new file as a whole.
#
# Also a fade away to 0 density is added
#

def info(BASE, resource):
    url = BASE+"resource/"+resource+"/info"
    http = urllib3.PoolManager()
    u = http.request('GET', url)
    data = u.data
    return json.loads(data)

def read(BASE, resource, box, depthBegin, depthEnd):
    url = BASE+'resource/' + resource + '/read?'
    url += 'bounds=%s&depthEnd=%s&depthBegin=%s&compress=false&offset=[85910,445600,50]' % (box, depthEnd, depthBegin)
    http = urllib3.PoolManager()
    u = http.request('GET', url)
    data = u.data
    return data

def readdata(BASE, resource, box, depthBegin, depthEnd):
    data = read(BASE, resource, box, depthBegin, depthEnd)
    #f = open('raw-greyhound-data','rb')
    #data = f.read()
    return data

def buildNumpyDescription(schema):
    output = {}
    formats = []
    names = []
    for s in schema:
        t = s['type']
        if t == 'floating':
            t = 'f'
        elif t == 'unsigned':
            t = 'u'
        else:
            t = 'i'

        f = '%s%d' % (t, int(s['size']))
        names.append(s['name'])
        formats.append(f)
    output['formats'] = formats
    output['names'] = names
    return output

def writeLASfile(dtype, data, filename):
    count = struct.unpack('<L',data[-4:])[0]


    # last four bytes are the count
    data = data[0:-4]
    d = np.ndarray(shape=(count,),buffer=data,dtype=dtype)
    try:
        minx = min(d['X'])
        miny = min(d['Y'])
        minz = min(d['Z'])
    except ValueError:
        print 'No points available in this bbox geometry'
        return

    header = laspy.header.Header()
    scale = 0.01
    header.x_scale = scale; header.y_scale = scale; header.z_scale = scale
    header.x_offset = minx ;header.y_offset = miny; header.z_offset = minz
    header.offset = [minx, miny, minz]

    X = (d['X'] - header.x_offset)/header.x_scale
    Y = (d['Y'] - header.y_offset)/header.y_scale
    Z = (d['Z'] - header.z_offset)/header.z_scale
    output = laspy.file.File(filename, mode='w', header = header)
    output.X = X
    output.set_scan_dir_flag(d['ScanDirectionFlag'])
    output.set_intensity(d['Intensity'])
    output.set_scan_angle_rank(d['ScanAngleRank'])
    output.set_pt_src_id(d['PointSourceId'])
    output.set_edge_flight_line(d['EdgeOfFlightLine'])
    output.set_return_num(d['ReturnNumber'])
    output.set_num_returns(d['NumberOfReturns'])
    output.Y = Y
    output.Z = Z
    output.Raw_Classification = d['Classification']
    output.close()

def implementation(camera_parameters = None):
    ### Preparation
    filenameList = []
    filenameDict = {}
    densityDict = {}
    bboxDict = {}
    
    ### Retrieve points from webserver
    downloadFromS3('jippe-home', 'POTREE_reads.txt', 'urls.txt')
    
    potreefile = open('urls.txt', 'r')
    for j, line in enumerate(potreefile):
        # extract params from READ request
        url = line
        parsed = urlparse.urlparse(url)
        params = urlparse.parse_qsl(parsed.query)
        dict_params = dict(params)
	resource = parsed.path.split('/')[2]

	# to make box an actual list:
	# import ast
	# ast.literal_eval(dict_params['bounds'])
	box = dict_params['bounds']
        depthBegin = int(dict_params['depthBegin'])
        depthEnd = int(dict_params['depthEnd'])
        
        if depthEnd - depthBegin != 1:
            startDepth = depthEnd
        
        # make sure all octree levers are 4 numbers
        filler = '0' * (4 - len(str(depthEnd)))
        depth = filler + str(depthEnd)
        
        # create filename with depth '0000' appended to front
        filename = '%soriginalfile%s.las' % (depth, j)
        filenameList.append(filename)
        
        # make filenamedict for merging with lasmerge
        if depth in filenameDict:
            appendfilename = filename + ' '
            filenameDict[depth] += appendfilename
        else:
            appendfilename = ' ' + filename + ' '
            filenameDict[depth] = appendfilename
            
        # retrieve from Greyhound webserver
	BASE = getGreyhoundServer()
	allinfo = info(BASE, resource)
	dtype = buildNumpyDescription(allinfo['schema'])

        data = readdata(BASE, resource, box, depthBegin, depthEnd)
        writeLASfile(dtype, data, filename)

    potreefile.close()

    # find camera offset
    camera_offset_command = "".join(('lasinfo -i ', filenameList[0], ' -nv -nmm -nco -o outputfile.txt'))
    os.system(camera_offset_command)
    with open('outputfile.txt') as f:
	for line in f:
	    if line[:14] == '  offset x y z':
		print(line)
		newline = line.split()
		camera_offset_params = float(newline[4]), float(newline[5]), float(newline[6])

    # Create a filename list with sorted filenameDict values
    levelfilenameList = []
    for key in filenameDict:
        levelfilenameList.append("".join((key,'.las')))
    levelfilenameList.sort()
    print(filenameList)

    # For each 'level' create 1 file
    for key in filenameDict:
        filenames = filenameDict[key]
        outname = "".join((key,'.las'))
        mergefiles = 'lasmerge -i ' + filenames + ' -o ' + outname
        os.system(mergefiles)

    # Cleanup
    for filename in filenameList:
        try:
            removeFile(filename)
        except OSError as e:
	    print(e)
            print '%s does not exist' % filename

    # Create one single file
    mergefiles = 'lasmerge -i *.las -o out.las'
    os.system(mergefiles)

    for filename in levelfilenameList:
	try:
	    removeFile(filename)
	except OSError as e:
	    print(e)
	    print('{} does not exist'.format(filename))
    ### Input camera parameters manually from url
    if camera_parameters == None:
	cameraorigin = (1000,-1800,100)
    else:
	cameraorigin = camera_parameters

    print(cameraorigin)
    print(camera_offset_params)

    ### Find formula for gradual density descent. This is implemented
    ### in more detail in other files in this folder. If needed copy
    ### the basics from there and continue.    
    
    #########################
    # Method implementation #
    #########################
    inFile = openLasFile('out.las')
    
    numpoints = len(inFile.points)
    print 'There are %s points in the original file' % numpoints
    
    goodpoints = np.vstack((inFile.x, inFile.y, inFile.z)).transpose()
    
    allpoints = []
    
    for i in range(len(goodpoints)):
      templist = []
      templist.append(goodpoints[i][0])
      templist.append(goodpoints[i][1])
      templist.append(goodpoints[i][2])
      allpoints.append(tuple(templist))
    
    used = [False] * len(allpoints)
    
    kdtree = scipy.spatial.KDTree(allpoints)
    
    methodpoints = set([])
    
    starttime1 = time.time()
    
    percentage = 0
    for j, point in enumerate(allpoints):
      if used[j] == True:
        continue
        
      distancevector = (point[0] - cameraorigin[0], point[1] - cameraorigin[1], point[2] - cameraorigin[2])
      distance = (distancevector[0] ** 2 + distancevector[1] ** 2 + distancevector[2] ** 2) ** 0.5
      
      # implement exponential function here
      # This should later be the density function
      nn = kdtree.query_ball_point(point, distance**0.2)
      
      appendvar = True
      
      for i in nn:
          if allpoints[i] in methodpoints:
              appendvar = False
              break
        
      if appendvar == True:
        methodpoints.add(point)
        for i in nn:
            used[i] = True
      
      newpercentage = int(j/float(numpoints)*100)
      if newpercentage > percentage:
        percentage = newpercentage
	if percentage == 1 or percentage % 10 == 0:
            print "Work in progress, %d%% done" % percentage
    
    endtime1 = time.time()
    timetaken1 = endtime1 - starttime1
    print 'There are %s points in the view frustum after vario-scale method application' % len(methodpoints)
    print 'This took %s seconds to calculate' % timetaken1
    
    methodpointx = []
    methodpointy = []
    methodpointz = []
    
    for point in methodpoints:
      methodpointx.append(point[0])
      methodpointy.append(point[1])
      methodpointz.append(point[2])
    
    print
    
    newoutput_file = File('method.las', mode = "w", header = inFile.header)
    newoutput_file.X = methodpointx
    newoutput_file.Y = methodpointy
    newoutput_file.Z = methodpointz
    
    newoutput_file.close()
    inFile.close()
    
    #######################
    convertLasZip('out.las', 'out.laz')
    convertLasZip('method.las', 'method.laz')
    
    uploadToS3('out.laz', 'jippe-greyhound-to-las-test-dense', "".join(('plasio_', resource, '_potree_original.laz')))
    uploadToS3('method.laz', 'jippe-greyhound-to-las-test-dense', "".join(('plasio_', resoure, '_potree_method.laz')))
    
    removeFile('out.las')
    removeFile('out.laz')
    removeFile('method.las')
    removeFile('method.laz')
    removeFile('urls.txt')
    removeFile('outputfile.txt')

@click.command()
@click.option('--camera_parameter', '-cp', type=(float,float,float), help='camera paramaters as specified by speck.ly')
def cli(camera_parameter):
    print(camera_parameter)
    implementation(camera_parameter)

if __name__ == '__main__':
    cli()
