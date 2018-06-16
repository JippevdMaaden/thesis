import urllib3
import numpy as np
import json
import struct
import laspy
import sys
import scipy.spatial
import time

from laspy.file import File

sys.path.insert(0, '/home/ec2-user/thesis')

from util.utils import *

#
# This file will test the vario_scale_1.py method for
# the POTREE request when the file tu-delft-campus is loaded
# url = http://potree.entwine.io/data/custom.html?s= ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/ &r= tu-delft-campus
# 
# The camera parameters are currently unknown, so currently
# a vario-scale implementation is done using arbitrary
# camera parameters.
#
def info(resource):
    url = BASE+"resource/"+resource+"/info"
    http = urllib3.PoolManager()
    u = http.request('GET', url)
    data = u.data
    return json.loads(data)

def read(resource, box, depthBegin, depthEnd):
    url = BASE+'resource/' + resource + '/read?'
    url += 'bounds=%s&depthEnd=%s&depthBegin=%s&compress=false&offset=[85910,445600,50]' % (box, depthEnd, depthBegin)
    http = urllib3.PoolManager()
    u = http.request('GET', url)
    data = u.data
    return data

def readdata():
    data = read(resource, box, depthBegin, depthEnd)
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

if __name__ == '__main__':
    resource = 'tu-delft-campus'
    BASE='http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/'
    allinfo = info(resource)
    dtype = buildNumpyDescription(allinfo['schema'])
    
    downloadFromS3('jippe-home', 'POTREE_reads.txt', 'urls.txt')
    
    potreefile = open('urls.txt', 'r')

    # from each line I need:
    # bounds = []
    # depthBegin = int
    # depthEnd = int
    # compress=false
    for j, line in enumerate(potreefile):
        print 'row %s' % j
        newline = line.split('&')
        box = newline[2].split('=')[1]
        depthBegin = newline[0].split('=')[1]
        depthEnd = newline[1].split('=')[1]
        
        filename = 'originalfile%s.las' % j
        data = readdata()
        writeLASfile(data, filename)
    
    potreefile.close()
    
    mergefiles = 'lasmerge -i *.las -o out.las'
    os.system(mergefiles)
    
    #cleanup
    print j
    for i in range(j):
        try:
            filename = 'originalfile%s.las' % i
            removeFile(filename)
        except OSError:
            print '%s does not exist' % filename
            
    # Unknown variables
    cameraorigin = [1000,-1800,100]
    
    
    ####################################
    ### Variable linear realtionship ###
    ####################################
    # The relationship is based on reaching the lowest density 
    # at the artefact (d2). When this artefact is reached.
    # This means the shortest distance to the artefact (Af)
    # must be identified
    #
    # The packingvariable is a guess between the max packing
    # variable for 2D circle packing (90%) and 3D sphere
    # packing (74%). This is done because the aerial LiDAR
    # point cloud is a 2.5D point cloud.
    #
    # methodvar = 1 / ( Af / ( ( packingvar / d2 ) / np.pi ) ** 0.5 )
    # First the area per point at the artefact is determined
    # by (packingvar / d2)
    # Secondly the radius per point at the artefact is determined
    # by (area / np.pi) ** 0.5
    # Thirdly the methodvariable is determined according to the
    # radius needed at the distance closest to the artefact
    # by 1 / ( Af / radius )
    methodvar = 0.01
    ########
    # Calc density
    ########
    baseDepth = allinfo['baseDepth']
    maxdensity = allinfo['density']
        
    countPerLevel = {}
    for i in range(18)[baseDepth:]:
          url = 'http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/count?depth=%d' % i
          http = urllib3.PoolManager()
          u = http.request('GET', url)
          temp = u.data
          print temp['points']
          print type(temp['points']
          countPerLevel[i] = 'nothing'
    print countPerLevel
    print maxdensity
    
    ########
   
    #Af = None
    #packingvar = 0.8
    #d2 = None
      
    #area = ( packingvar / d2 )
    #radius = ( area / np.pi ) ** 0.5
    #methodvar = 1 / ( Af / radius )
    ####################################
        
        
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
      
      
      
      nn = kdtree.query_ball_point(point, distance * methodvar)
      
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
    
    uploadToS3('out.laz', 'jippe-greyhound-to-las-test-dense', 'potree_original.laz')
    uploadToS3('method.laz', 'jippe-greyhound-to-las-test-dense', 'potree_method.laz')
    
    removeFile('out.las')
    removeFile('out.laz')
    removeFile('method.las')
    removeFile('method.laz')
    removeFile('urls.txt')
