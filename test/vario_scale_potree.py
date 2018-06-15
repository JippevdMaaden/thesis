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
    BASE='http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/'
    allinfo = info(resource)
    rng = 200
    fov = 120
    
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=0&depthEnd=9&bounds=[-187000,-187000,-187000,187000,187000,187000]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile0.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=9&depthEnd=10&bounds=[0,-187000,0,187000,0,187000]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile1.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=9&depthEnd=10&bounds=[-187000,-187000,0,0,0,187000]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile2.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=9&depthEnd=10&bounds=[0,-187000,-187000,187000,0,0]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile3.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=9&depthEnd=10&bounds=[-187000,0,0,0,187000,187000]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile4.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=9&depthEnd=10&bounds=[-187000,-187000,-187000,0,0,0]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile5.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=9&depthEnd=10&bounds=[0,0,-187000,187000,187000,0]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile6.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=9&depthEnd=10&bounds=[-187000,0,-187000,0,187000,0]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile7.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=10&depthEnd=11&bounds=[0,-93500,0,93500,0,93500]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile8.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=10&depthEnd=11&bounds=[-93500,-93500,0,0,0,93500]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile9.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=10&depthEnd=11&bounds=[93500,-187000,-93500,187000,-93500,0]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile10.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=10&depthEnd=11&bounds=[93500,-187000,-93500,187000,-93500,0]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile11.las')
    #writeLASfile(read('http://ec2-54-93-79-134.eu-central-1.compute.amazonaws.com:8080/resource/tu-delft-campus/read?depthBegin=10&depthEnd=11&bounds=[0,-93500,-93500,93500,0,0]&schema=[{%22name%22:%22X%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Y%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Z%22,%22size%22:4,%22type%22:%22signed%22},{%22name%22:%22Intensity%22,%22size%22:2,%22type%22:%22unsigned%22},{%22name%22:%22Classification%22,%22size%22:1,%22type%22:%22unsigned%22}]&compress=true&scale=0.01&offset=[85910,445600,50]'), 'originalfile12.las')
    
    downloadFromS3('jippe-home', 'POTREE_reads.txt', 'urls.txt')
    
    potreefile = open('urls.txt', 'r')
    for line in potreefile:
        print line
    
