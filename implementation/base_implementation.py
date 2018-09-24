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
# The implemented method uses automatic processing as described
# during my P3 presentation
#
# This file contains the base class that is used for further development
#

class MethodBase():
    """
    Base implementation class
    """
    
    def __init__(self, camera_origin, filename_dict):
        self.camera_origin = camera_origin
        self.filename_dict = filename_dict

    def determine_density(self):
        densityDict = {}
        bboxDict = {}

        ### Determine density jumps between levels
        #for each file do os.system(lasinfo -i inputfile.las -compute_density -nh -nv -nmm -nco -o outputfile.txt)
        # Determine density per level, and bbox per level
        for key in filenameDict:
            filename = key + '.las'
            outname = key + '.txt'
            densityfiles = 'lasinfo -i ' + filename + ' -compute_density -nv -nmm -nco -o ' + outname
            os.system(densityfiles)

        #create dict with density for each level (old), using lasinfo gives some weird results
        for key in filenameDict:
            filename = key + '.txt'
            densityfile = open(filename, 'r')
            for line in densityfile:
                if line[:13] == 'point density':
                    newline = line.split()
                    density = float(newline[4])
                    densityDict[key] = density
            densityfile.close()

        #create dict with bbox for each level (using -nh)
        for key in filenameDict:
            bboxDict[key] = {}
            filename = key + '.txt'
            densityfile = open(filename, 'r')
            for line in densityfile:
                if line[:11] == '  min x y z':
                    newline = line.split()
                    bboxDict[key]['xmin'] = float(newline[4])
                    bboxDict[key]['ymin'] = float(newline[5])
                    bboxDict[key]['zmin'] = float(newline[6])
                if line[:11] == '  max x y z':
                    newline = line.split()
                    bboxDict[key]['xmax'] = float(newline[4])
                    bboxDict[key]['ymax'] = float(newline[5])
                    bboxDict[key]['zmax'] = float(newline[6])
            densityfile.close()

        #create dict with density estimation for each level
        for key in filenameDict:
            filename = key + '.txt'
            densityfile = open(filename, 'r')
            for line in densityfile:
                if line[:25] == '  number of point records':
                    newline = line.split()
                    numpoints = int(newline[4])
            densityfile.close()
            areathislevel = (abs(bboxDict[key]['xmin']) + bboxDict[key]['xmax']) * (abs(bboxDict[key]['ymin']) + bboxDict[key]['ymax'])
            densthislevel = numpoints / areathislevel
            densityDict[key] = densthislevel
            
        return densityDict

    def determine_gradual_descent_formula(self, densityDict):
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
        densjumpDict = {}
        furthestcornersDict = {}
        for i, level in enumerate(densjumpList[:-1]):
            bbox = bboxDict[densjumpList[i+1]]
            distx = [(abs(self.camera_origin[0] - bbox['xmin']), 'xmin'), (abs(self.camera_origin[0] - bbox['xmax']), 'xmax')]
            disty = [(abs(self.camera_origin[1] - bbox['ymin']), 'ymin'), (abs(self.camera_origin[1] - bbox['ymax']), 'ymax')]
            distz = [(abs(self.camera_origin[2] - bbox['zmin']), 'zmin'), (abs(self.camera_origin[2] - bbox['zmax']), 'zmax')]
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

        #minimal distance jump between level and level+1
            print mindist
            densjumpDict[level] = mindist

        print densjumpDict
        print 'from density 0011 to 0010 the jump from {} to {} has to be made within {} units'.format(densityDict['0011'], densityDict['0010'], densjumpDict['0010'])

        return densjumpDict
        
    def base_method(self, file_name):
        """"
        Base method implementation
        """
        #########################
        # Method implementation #
        #########################
        inFile = openLasFile(filename)

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

          distancevector = (point[0] - self.camera_origin[0], point[1] - self.camera_origin[1], point[2] - self.camera_origin[2])
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

        newoutput_file = File('method.las', mode = "w", header = inFile.header)
        newoutput_file.X = methodpointx
        newoutput_file.Y = methodpointy
        newoutput_file.Z = methodpointz

        newoutput_file.close()
        inFile.close()

        #######################
        convertLasZip(filename, 'out.laz')
        convertLasZip('method.las', 'method.laz')

        uploadToS3('out.laz', 'jippe-greyhound-to-las-test-dense', 'potree_original.laz')
        uploadToS3('method.laz', 'jippe-greyhound-to-las-test-dense', 'potree_method.laz')

        removeFile(filename)
        removeFile('out.laz')
        removeFile('method.las')
        removeFile('method.laz')
