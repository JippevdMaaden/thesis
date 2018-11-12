"""
This file is used to test the barebones implementation used to create a point cloud (.las) file
from a Greyhound request.
"""

import laspy
import numpy as np
from urllib2 import urlopen
import urlparse
import json
import struct
import sys
import scipy.spatial

sys.path.insert(0, '/home/ec2-user/thesis')

from util.utils import * 
from results.set_params import get_global_param_dict

def writeLASfile(data, filename):

    minx = min(data['X'])
    miny = min(data['Y'])
    minz = min(data['Z'])

    header = laspy.header.Header()
    scale = 0.01
    header.x_scale = scale; header.y_scale = scale; header.z_scale = scale
    header.x_offset = minx ;header.y_offset = miny; header.z_offset = minz
    header.offset = [minx, miny, minz]

    X = (data['X'] - header.x_offset)/header.x_scale
    Y = (data['Y'] - header.y_offset)/header.y_scale
    Z = (data['Z'] - header.z_offset)/header.z_scale
    output = laspy.file.File(filename, mode='w', header = header)
    output.X = X
    output.set_scan_dir_flag(data['ScanDirectionFlag'])
    output.set_intensity(data['Intensity'])
    output.set_scan_angle_rank(data['ScanAngleRank'])
    output.set_pt_src_id(data['PointSourceId'])
    output.set_edge_flight_line(data['EdgeOfFlightLine'])
    output.set_return_num(data['ReturnNumber'])
    output.set_num_returns(data['NumberOfReturns'])
    output.Y = Y
    output.Z = Z
    output.Raw_Classification = data['Classification']
    output.close()

class Resource(object):

    def __init__(self, base, name):

        self.name = name
        self.url = base
        self.info = self.get_info()


    def get_info(self, data=None):

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

        if not data:
            command = self.url + "/info"
            u = urlopen(command)
            data = u.read()
        j = json.loads(data)
        j['dtype'] = buildNumpyDescription(j['schema'])
        return j


    def read(self, bounds, depthBegin, depthEnd, scale, offset):
        import json
        import numpy as np

        
        command = self.url + '/read?' + 'bounds={}&depthBegin={}&depthEnd={}&compress=false&scale={}&offset={}'.format(bounds, depthBegin, depthEnd, scale, offset)
        # command = self.url + '/read?'

        # command += 'bounds=%5B0%2C-628000%2C-628000%2C628000%2C0%2C0%5D&depthBegin=8&depthEnd=9&compress=false&scale=[0.01,0.01,0.01]&offset=[85000,443750,50]'
        try:
            u = urlopen(command)
        except HTTPError:
            print('This command failed: {}'.format(command)) 
        data = u.read()

        # last four bytes are the point count
        count = struct.unpack('<L',data[-4:])[0]

        array = np.ndarray(shape=(count,),buffer=data,dtype=self.info['dtype'])
        return array


def main():
    """
    
    """
    global_param_dict = get_global_param_dict()
    
    downloadFromS3('jippe-home', global_param_dict['potree_file'], 'urls.txt')

    potreefile = open('urls.txt', 'r')
    for j, line in enumerate(potreefile):
        # extract params from READ request
        print(j)
        url = line
        parsed = urlparse.urlparse(url)
        params = urlparse.parse_qsl(parsed.query)
        dict_params = dict(params)
        base = "http://" + parsed[1] + "/resource/municipality-delft"

        r = Resource(base, 'test')
        data = r.read(dict_params['bounds'], dict_params['depthBegin'], dict_params['depthEnd'], dict_params['scale'], dict_params['offset'])
        datafilename = str(j) + 'testfile.las'
        writeLASfile(data, datafilename)
        #uploadToS3('testfile.las', 'jippe-home', 'testfile.las')

    os.system('lasmerge -i *.las -o original.las')
    uploadToS3('original.las', 'jippe-home','original.las')
    os.system('rm *.las')

if __name__ == "__main__":
    main()
