import urllib3
import numpy as np
import json
import struct
import laspy
import sys
import scipy.spatial
import time
import random

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
    
    allpoints = []
    
    for i in range(len(goodpointx)):
      templist = []
      templist.append(goodpointx[i])
      templist.append(goodpointy[i])
      templist.append(goodpointz[i])
      allpoints.append((templist))
    
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
        area1 = np.pi * int(key) ** 2
        area2 = np.pi * ( int(key) + 1 ) ** 2
        area = area2 - area1 / ( 360 / float(fov) )
#        volume = abs(bbox[0][0] - bbox[1][0]) * abs(bbox[0][1] - bbox[1][1]) + abs(bbox[0][2] - bbox[1][2])
        volume = area * abs(bbox[0][2] - bbox[1][2])
        numpoints = len(distdict[key])
        try:
            density = float(numpoints) / float(volume)
        except ZeroDivisionError:
            print "ZeroDivisionErro when calculation density"
            density = 999
        densdict[key] = density
    
    denslist = []
    for key in densdict:
        denslist.append((int(key), densdict[key]))
    
    denslist.sort()
    
    print len(allpoints)
    
    # remove every 10th meter of points
    #for key in densdict:
    #    if int(key) % 10 == 0:
    #        for point in distdict[key]:
    #            allpoints.remove(point)
                
    # remove using exponential formula where 0 -> 1 and 100 -> 0.001
    # TODO
    
    
    ###########
    # Numpy is way faster than list removal, 0.02 seconds vs 699 seconds
    #starttime1 = time.time()
    # remove so that every bin has 100 points in it using numpy array
    #newallpoints = np.array([]).reshape(0,3)
    #for key in distdict:
    #    if len(distdict[key]) > 100:
    #        newallpoints = np.append(newallpoints, distdict[key][:100], axis = 100)
    #    else:
    #        newallpoints = np.append(newallpoints, distdict[key], axis = 100)
    #endtime1 = time.time()
    
    #starttime2 = time.time()
    # remove so that every bin has 100 points in it using list remove
    #for key in distdict:
    #    if len(distdict[key]) > 100:
    #        for point in distdict[key][100:]:
    #            allpoints.remove(point)
                
    #endtime2 = time.time()
    
    #totaltime1 = endtime1 - starttime1
    #totaltime2 = endtime2 - starttime2
    
    #print 'Using numpy takes {} seconds, and results in {} points'.format(totaltime1, len(newallpoints))
    #print 'using list takes {} seconds, and results in {} points'.format(totaltime2, len(allpoints))
    
    newallpoints = np.array([]).reshape(0,3)
    for key in distdict:
        if len(distdict[key]) > 500:
            temppoints = random.sample(distdict[key], 500)
            newallpoints = np.append(newallpoints, np.array(temppoints), axis = 0)
        else:
            newallpoints = np.append(newallpoints, distdict[key], axis = 0)
    
    print len(newallpoints)
    
    # Save to file
    goodpointx = []
    goodpointy = []
    goodpointz = []
    
    for point in newallpoints:
      if viewfrustum.isVisible([point[0], point[1], point[2]]):
        goodpointx.append(point[0])
        goodpointy.append(point[1])
        goodpointz.append(point[2])
    
    print 'There are %s points left when using the method' % len(goodpointx)    
    
    method_file = File('methodfile.las', mode = "w", header = inFile.header)
    method_file.X = goodpointx
    method_file.Y = goodpointy
    method_file.Z = goodpointz
    
    
    #########################
    
    inFile.close()
    output_file.close()
    method_file.close()
    
    convertLasZip('originalfile.las', 'originalfile.laz')
    convertLasZip('frustumfile.las', 'frustumfile.laz')
    convertLasZip('methodfile.las', 'methodfile.laz')
    
    uploadToS3('originalfile.laz', 'jippe-greyhound-to-las-test-dense', 'greyhound_to_las_test_original.laz')
    uploadToS3('frustumfile.laz', 'jippe-greyhound-to-las-test-dense', 'greyhound_to_las_test_frustum.laz')
    uploadToS3('methodfile.laz', 'jippe-greyhound-to-las-test-dense', 'greyhound_to_las_test_method.laz')
    
    removeFile('originalfile.las')
    removeFile('originalfile.laz')
    removeFile('frustumfile.las')
    removeFile('frustumfile.laz')
    removeFile('methodfile.las')
    removeFile('methodfile.laz')
