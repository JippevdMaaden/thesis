"""
Implementation of the lineair method
"""


import numpy as np
import laspy
import sys
import scipy.spatial
import urlparse
import math


sys.path.insert(0, '/home/ec2-user/thesis')

from util.utils import *
from results.set_params import get_global_param_dict


def find_vector(alpha, beta):
    """
    
    """
    a, b = math.radians(alpha), math.radians(beta)
    x = 1 * math.sin(a) * math.cos(b)
    y = -1 * math.cos(a) * math.cos(b)
    z = math.sin(b)
    return (x, y, z)

def main():
    """
    
    """
    downloadFromS3('jippe-home', 'original.las', 'original.las')
    inFile = openLasFile('original.las')
    numpoints = len(inFile.points)
    print('There are {} points in the original file'.format(numpoints))
    
    goodpoints = np.vstack((inFile.x, inFile.y, inFile.z)).transpose()

    used = [False] * numpoints

    print('Creating kdtree')    
    kdtree = scipy.spatial.cKDTree(goodpoints, leafsize=2)
    print('Done creating kdtree')

    global_param_dict = get_global_param_dict()

    # Find camera origin
    speckly_url = global_param_dict['camera_url'] 
    parsed = urlparse.urlparse(speckly_url)
    params = urlparse.parse_qsl(parsed.query)
    dict_params = dict(params)
    
    # what is in dict_params:
    # ps = point size
    # pa = point size attenuation (closer to you appear larger)
    # ca = camera rotation xy (z-axis)
    # ce = camera rotation yz (x-axis)
    # cd = camera distance to target
    # s = server
    # r = resource
    # ze = Z-exaggeration
    # c0s = imagery
    # ct = camera target
    # for key, value in dict_params.items():
    #     print('For key: {}, the value is: {}'.format(key, value))
    
    camera_target = dict_params['ct'].split(',')
    print('The camera target is {}'.format(camera_target))
 
    camera_vector = find_vector(float(dict_params['ca']), float(dict_params['ce']))
    print('The camera vector is {}'.format(camera_vector))
    camera_vector_distance = tuple(x * float(dict_params['cd']) for x in camera_vector)
    print('The camera_vector_distance is {}'.format(camera_vector_distance))
    camera_location = (float(camera_target[0]) + camera_vector_distance[0],
                       float(camera_target[1]) + camera_vector_distance[1],
                       float(camera_target[2]) + camera_vector_distance[2])
    print('The camera location is {}'.format(camera_location))
 
    ##############################
    # This is the lineair method #
    ##############################
    method_variable = global_param_dict['var_linear']
    method = lambda distance : distance * method_variable
    ##############################
    allpoints = [(point[0], point[1], point[2]) for point in goodpoints]
    
    methodpoints = set([])
    for j, point in enumerate(allpoints):
        # continue if the point has been used as nn for other points
        if used[j] == True:
            continue
        # get point distance from camera
        distance_vector = [point[0], camera_location[0],
                           point[1], camera_location[1],
                           point[2], camera_location[2]]
        point_distance = (distance_vector[0] ** 2 +
                          distance_vector[1] ** 2 +
                          distance_vector[2] ** 2) ** 0.5

        # determine nn using the method
        nn = kdtree.query_ball_point(point, method(point_distance))

        appendvar = True
        for i in nn:
            if allpoints[i] in methodpoints:
                appendvar = False
                break
        
        if appendvar == True:
            point_tuple = (point[0], point[1], point[2], method(point_distance))
            methodpoints.add(point_tuple) 
            for i in nn:
                used[i] = True

    methodpointx = [point[0] for point in methodpoints]
    methodpointy = [point[1] for point in methodpoints]
    methodpointz = [point[2] for point in methodpoints]
    methodpointi = [point[3] for point in methodpoints]
    
    print('There are {} points in the method_file'.format(len(methodpoints)))
    # we have to make the scale and offset correct for the points first.
    # 1. remove the offset
    # 2. divide by the scale 
    offset = inFile.header.offset
    scale = inFile.header.scale
    methodpoint_remove_offset = None
    
    methodpointX = [((point[0] - offset[0]) / scale[0]) for point in methodpoints]
    methodpointY = [((point[1] - offset[1]) / scale[1]) for point in methodpoints]
    methodpointZ = [((point[2] - offset[2]) / scale[2]) for point in methodpoints]
    methodpointi = [point[3] for point in methodpoints]

    newoutput_file = File('method.las', mode = "w", header = inFile.header)
    newoutput_file.X = methodpointX
    newoutput_file.Y = methodpointY
    newoutput_file.Z = methodpointZ
    newoutput_file.intensity = methodpointi
    newoutput_file.close()
    inFile.close()
    
    uploadToS3('method.las', 'jippe-home', 'method.las')
    os.system('rm *.las')
    os.system('rm *.txt')

if __name__ == "__main__":
    main()
