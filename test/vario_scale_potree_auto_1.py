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
# The implemented method uses a logarithmic(e) function to describe
# which points should be removed
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
    ### Preparation
    resource = 'tu-delft-campus'
    BASE = getGreyhoundServer()
    allinfo = info(resource)
    dtype = buildNumpyDescription(allinfo['schema'])
    filenameList = []
    filenameDict = {}
    densityDict = {}
    bboxDict = {}
    
    ### Retrieve points from webserver
    downloadFromS3('jippe-home', 'POTREE_reads.txt', 'urls.txt')
    
    potreefile = open('urls.txt', 'r')
    for j, line in enumerate(potreefile):
        # extract data to retrieve from Greyhound webserver
 #       print 'row %s' % j
        newline = line.split('&')
        box = newline[2].split('=')[1]
        depthBegin = newline[0].split('=')[1]
        depthEnd = newline[1].split('=')[1]
        
        if int(depthEnd) - int(depthBegin) != 1:
            startDepth = depthEnd
        
        # make sure all octree levers are 4 numbers
        filler = '0' * (4 - len(depthEnd))
        depth = filler + depthEnd
        
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
        data = readdata()
        writeLASfile(data, filename)
    
#    print filenameDict
    potreefile.close()
    
    #for each 'level' create 1 file
    for key in filenameDict:
        filenames = filenameDict[key]
        outname = key + '.las'
        mergefiles = 'lasmerge -i ' + filenames + ' -o ' + outname
#        print mergefiles
        os.system(mergefiles)

    #cleanup
    for filename in filenameList:
        try:
            removeFile(filename)
        except OSError:
            print '%s does not exist' % filename
            
    ### Retrieve camera parameters from webviewer
    cameraorigin = [1000,-1800,100]
    
    ### Determine point distance from camera
    # is this needed? Might depend on method implementation later on
    
    ### Determine density jumps between levels
    #for each file do os.system(lasinfo -i inputfile.las -compute_density -nh -nv -nmm -nco -o outputfile.txt)
    # Determine density per level, and bbox per level
    for key in filenameDict:
        filename = key + '.las'
        outname = key + '.txt'
        densityfiles = 'lasinfo -i ' + filename + ' -compute_density -nv -nmm -nco -o ' + outname
#        print densityfiles
        os.system(densityfiles)
    
    #create dict with density for each level
    for key in filenameDict:
        filename = key + '.txt'
        densityfile = open(filename, 'r')
        for line in densityfile:
            if line[:13] == 'point density':
#                print line
                newline = line.split()
                density = float(newline[4])
                densityDict[key] = density
        densityfile.close()
#    print densityDict
    
    #create dict with bbox for each level (using -nh)
    for key in filenameDict:
        bboxDict[key] = {}
        filename = key + '.txt'
        densityfile = open(filename, 'r')
        for line in densityfile:
            if line[:11] == '  min x y z':
#                print line
                newline = line.split()
                bboxDict[key]['xmin'] = float(newline[4])
                bboxDict[key]['ymin'] = float(newline[5])
                bboxDict[key]['zmin'] = float(newline[6])
            if line[:11] == '  max x y z':
#                print line
                newline = line.split()
                bboxDict[key]['xmax'] = float(newline[4])
                bboxDict[key]['ymax'] = float(newline[5])
                bboxDict[key]['zmax'] = float(newline[6])
        densityfile.close()
#    print bboxDict
            
    ### Find formula for gradual density decent from jump to jump
    # find 'same' bounding boxes, where multiple levels cover the same area
    filenameList = []
    for key in filenameDict:
        filenameList.append(key)
    filenameList.sort()
    
    densjumpList = []
    for i, level in enumerate(filenameList[:-1]):
        nextlevel = filenameList[i+1]
        areathislevel = (abs(bboxDict[level]['xmin']) + bboxDict[level]['xmax']) * (abs(bboxDict[level]['ymin']) + bboxDict[level]['ymax'])
        areanextlevel = (abs(bboxDict[nextlevel]['xmin']) + bboxDict[nextlevel]['xmax']) * (abs(bboxDict[nextlevel]['ymin']) + bboxDict[nextlevel]['ymax'])
        areajump = areathislevel / areanextlevel
        
        # if they cover the same area, add them together or just note that they are the same????
        if int(areajump) == 1:
            print 'there is no bbox jump from level %s to level %s' % (level, nextlevel)
        else:
            if level not in densjumpList:
                densjumpList.append(level)
            if nextlevel not in densjumpList:
                densjumpList.append(nextlevel)
            
    
        
    # determine closest distance where the density of level X has to start
    # for the highest level this would be at the bbox edge closest to the camera
    
    # for the other levels this would not be the bbox edge, since this is the same as the highest level
    # for the other levels a plane has to be formed where the level+1 ends, and thus the level density begins
    # there can be 1 to 4 planes created this way. For each of those planes the shortest distance towards it
    # must be calculated. The minimum distance is the distance we're looking for
    
    # for each camera parameter determine dist distance from min and max of the level
    # the bigger distance of the two is where the next level can 'start'
    
    furthestcornersDict = {}
    for i, level in enumerate(densjumpList[:-1]):
        bbox = bboxDict[densjumpList[i+1]]
        distx = [(abs(cameraorigin[0] - bbox['xmin']), 'xmin'), (abs(cameraorigin[0] - bbox['xmax']), 'xmax')]
        disty = [(abs(cameraorigin[1] - bbox['ymin']), 'ymin'), (abs(cameraorigin[1] - bbox['ymax']), 'ymax')]
        distz = [(abs(cameraorigin[2] - bbox['zmin']), 'zmin'), (abs(cameraorigin[2] - bbox['zmax']), 'zmax')]
        print max(distx)
        print max(disty)
        print max(distz)
        
        furthestcornersDict['max max max'] = [(max(distx)[1],  max(disty)[1], max(distz)[1]), ((max(distx)[0]) ** 2 + (max(disty)[0]) ** 2 + (max(distz)[0]) ** 2) ** 0.5]
        furthestcornersDict['min max max'] = [(min(distx)[1],  max(disty)[1], max(distz)[1]), ((min(distx)[0]) ** 2 + (max(disty)[0]) ** 2 + (max(distz)[0]) ** 2) ** 0.5]
        furthestcornersDict['max min max'] = [(max(distx)[1],  min(disty)[1], max(distz)[1]), ((max(distx)[0]) ** 2 + (min(disty)[0]) ** 2 + (max(distz)[0]) ** 2) ** 0.5]
        furthestcornersDict['max max min'] = [(max(distx)[1],  max(disty)[1], min(distz)[1]), ((max(distx)[0]) ** 2 + (max(disty)[0]) ** 2 + (min(distz)[0]) ** 2) ** 0.5]
        print furthestcornersDict
        mindist = None
        for key in furthestcornersDict:
            if mindist == None:
                mindist = furthestcornersDict[key][1]
            else:
                if mindist > furthestcornersDict[key][1]:
                    mindist = furthestcornersDict[key][1]
        print mindist
            
        
        
    
    
    ### Use formula to filter points accordingly
    
    #test upload files to S3
    uploadToS3('0009.las', 'jippe-test', '0009.las')
    uploadToS3('0010.las', 'jippe-test', '0010.las')
    uploadToS3('0011.las', 'jippe-test', '0011.las')
    #
    
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
      
      # implement logarithmic(e) function here
      nn = kdtree.query_ball_point(point, np.log(distance*0.5))
      
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
