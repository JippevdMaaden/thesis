import urllib3
import numpy as np
import json
import struct
import laspy
import sys
import scipy.spatial
import time
import matplotlib.pyplot as plt

from operator import itemgetter
from laspy.file import File

sys.path.insert(0, '/home/ec2-user/thesis')

from util.utils import *

#
# This file will test the folling method by requesting a
# complete dataset from the Greyhound server, determining
# which points are inside the view frustum and lastly
# determining which points should be kept according to the
# method:
#
# By sorting all points based on distance from the camera
# origin, blocks can be made (similar to a histogram).
# The density per block can then be determined accourding
# by removing random samples from each block.
#

def info(resource):
    url = BASE+"resource/"+resource+"/info"
    http = urllib3.PoolManager()
    u = http.request('GET', url)
    data = u.data
    return json.loads(data)

def read(resource, rng, depth):

    lr = [center[0] - rng, center[1] - rng]
    ul = [center[0] + rng, center[1] + rng]
    z0 = 0 - rng
    z1= 0 + rng

    box = '['+ ','.join([str(i) for i in [lr[0], lr[1], z0, ul[0], ul[1], z1]]) + ']'
    url = BASE+'resource/' + resource + '/read?'
    url += 'bounds=%s&depthEnd=%d&depthBegin=%d&compress=false' % (box,depth[1],depth[0])
    http = urllib3.PoolManager()
    u = http.request('GET', url)
    data = u.data
    return data

def readdata():
    data = read(resource, rng, depth)
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

def writeLASfile(data, filename):
    count = struct.unpack('<L',data[-4:])[0]


    # last four bytes are the count
    data = data[0:-4]
    d = np.ndarray(shape=(count,),buffer=data,dtype=dtype)
    minx = min(d['X'])
    miny = min(d['Y'])
    minz = min(d['Z'])

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

if __name__ == '__main__':
    resource = 'tu-delft-campus'
    BASE = getGreyhoundServer()
    allinfo = info(resource)
    rng = 200
    fov = 120
    
    _3Dcenter = (allinfo['offset'][0], allinfo['offset'][1], allinfo['offset'][2])
    center = [_3Dcenter[0], _3Dcenter[1]]
    basedepth = allinfo['baseDepth']

    depth = [7,13]
    dtype = buildNumpyDescription(allinfo['schema'])
    data = readdata()
    
    writeLASfile(data, 'originalfile.las')
    
    goodpoints = []
    
    # override raw_input for testing
    cameraorigin = (85910, 445600, 0)
    cameratarget = (85910, 445600, -1)
    viewfrustum = CameraCone(_3Dcenter, cameraorigin, cameratarget, fov)
    
    inFile = openLasFile('originalfile.las')
    
    print 'There are %s points in the original file' % len(inFile.points)
    
    allpoints = np.vstack((inFile.x, inFile.y, inFile.z)).transpose()
    
    goodpointx = []
    goodpointy = []
    goodpointz = []
    
    for point in allpoints:
      if viewfrustum.isVisible([point[0], point[1], point[2]]):
        goodpointx.append(point[0])
        goodpointy.append(point[1])
        goodpointz.append(point[2])
    
    print 'There are %s points in the view frustum' % len(goodpointx)    
    
    output_file = File('frustumfile.las', mode = "w", header = inFile.header)
    output_file.X = goodpointx
    output_file.Y = goodpointy
    output_file.Z = goodpointz
    
    #########################
    # Method implementation #
    #########################
    distdict = {}
    
    for point in allpoints:
      distancevector = (point[0] - cameraorigin[0], point[1] - cameraorigin[1], point[2] - cameraorigin[2])
      distance = (distancevector[0] ** 2 + distancevector[1] ** 2 + distancevector[2] ** 2) ** 0.5
      
      dictkey = '%s' % int(distance)
      if dictkey not in distdict:
        distdict[dictkey] = [point]
      else:
        distdict[dictkey].append(point)
      
    maxdict = {}
    for key in distdict:
        templist = distdict[key][:5]
        sortedx = sorted(templist, key=itemgetter(0))
        sortedy = sorted(templist, key=itemgetter(1))
        sortedz = sorted(templist, key=itemgetter(2))
        maxdict[key] = [(sortedx[0][0], sortedy[0][1], sortedz[0][2]), (sortedx[-1][0], sortedy[-1][1], sortedz[-1][2])]     
        
    densdict = {}
    for key in maxdict:
        bbox = maxdict[key]
        volume = abs(bbox[0][0] - bbox[1][0]) * abs(bbox[0][1] - bbox[1][1]) + abs(bbox[0][2] - bbox[1][2])
        numpoints = len(distdict[key])
        density = float(numpoints) / float(volume)
        densdict[key] = density
    
    for key in densdict:
        print densdict[key]
    # Plot the histogram before method operation
    
    #########################
    
    inFile.close()
    
    convertLasZip('originalfile.las', 'originalfile.laz')
    
    uploadToS3('originalfile.laz', 'jippe-greyhound-to-las-test-dense', 'greyhound_to_las_test_original.laz')
    
    removeFile('originalfile.las')
    removeFile('originalfile.laz')