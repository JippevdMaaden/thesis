import urllib3
import sys
import json
import struct
import numpy as np
import io
import requests

from bitstream import BitStream
from flask import Flask, send_file, make_response
from flask_restful import Resource, Api, reqparse

sys.path.insert(0, '/home/ec2-user/thesis')

from util.utils import *

app = Flask(__name__)
api = Api(app)

prefix_resource = '/resource/municipality-delft'
greyhoud_server = getGreyhoundServer()

def info(resource):
    url = greyhoud_server[:-1] + prefix_resource + '/info'
    
    http = urllib3.PoolManager()
    u = http.request('GET', url)
    data = u.data
    return json.loads(data)

def read(url):
    http = urllib3.PoolManager()
    u = http.request('GET', url)
    data = u.data
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


def writeLASfile(data, filename, dtype):
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

class Greyhound_read(Resource):
    # to debug this Class I probably will have to solve the error:
    #
    # UnicodeDecodeError: 'utf8' codec can't decode byte 0xd9 in position 0: invalid continuation byte
    #
    # Most probably I will have to unpack the datastream to LAZ files, see test folder
    # and then use PotreeConverter to create a datastream again
    # then send that as 'return'
    
  def get(self):
    parser = reqparse.RequestParser()
    parser.add_argument('depthEnd', type=str)
    parser.add_argument('depthBegin', type=str)
    parser.add_argument('bounds', type=str)
    parser.add_argument('scale', type=str)
    parser.add_argument('offset', type=str)
    parser.add_argument('schema', type=str)
    parser.add_argument('compress', type=str)
    
    temp_dict = parser.parse_args()
    
    # remove arguments not in the original query
    remove_args = []
    for key in temp_dict:
      if temp_dict[key] == None:
        remove_args.append(key)
        
    # remove schema from dict for now
    file_schema = temp_dict['schema']
    remove_args.append('schema')
    print file_schema
    print type(file_schema)

    new_schema = json.loads(file_schema)
    print new_schema
    print type(new_schema)
    print new_schema[0]

    for key in remove_args:
      del temp_dict[key]
    
    # parse arguments so they can be appended to the url-string
    greyhound_dict = {}
    for key in temp_dict:
      new_var = key + '=' + temp_dict[key] + '&'
      greyhound_dict[key] = new_var

    # append args to the url-string
    greyhound_string_to_add = ''
    for key in greyhound_dict:
      greyhound_string_to_add += greyhound_dict[key]

    # remove the last '&' from the url-string
    string_to_add = greyhound_string_to_add[:-1]

    # create full url-string
    greyhound_server = getGreyhoundServer()
    server_to_call = '{}{}/read?{}'.format(greyhound_server[:-1], prefix_resource, string_to_add)

    # call greyhound server, save each file
    data = read(server_to_call)

    filename = '{} {} {}'.format(temp_dict['depthBegin'], temp_dict['depthEnd'], temp_dict['bounds'])

    writeLASfile(data, filename, buildNumpyDescription(new_schema))

    return None


class Greyhound_info(Resource):
  def get(self):
    # create full url-string
    greyhound_server = getGreyhoundServer()
    server_to_call = '{}{}/info'.format(greyhound_server[:-1], prefix_resource)
    data = read(server_to_call)
    json_read = json.loads(data)
    json_write = json.dumps(json_read)

    resp = app.response_class(response=json_write, status=200, mimetype='application/json')

    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE'
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Connection'] = 'keep-alive'
    resp.headers['X-powered-by'] = 'Jippe van der Maaden'
    return resp

class Greyhound_hierarchy(Resource):
    # getting the same error as the Greyhound_read Class, which is weird
    # Will have to dive deeper into this issue
  def get(self):
    parser = reqparse.RequestParser()
    parser.add_argument('depthEnd', type=str)
    parser.add_argument('depthBegin', type=str)
    parser.add_argument('bounds', type=str)
    parser.add_argument('scale', type=str)
    parser.add_argument('offset', type=str)
    
    temp_dict = parser.parse_args()
    
    # remove arguments not in the original query
    remove_args = []
    for key in temp_dict:
      if temp_dict[key] == None:
        remove_args.append(key)
    
    for key in remove_args:
      del temp_dict[key]
    
    # parse arguments so they can be appended to the url-string
    for key in temp_dict:
      new_var = key+ '=' + temp_dict[key] + '&'
      temp_dict[key] = new_var
    
    # append args to the url-string
    temp_string_to_add = ''
    for key in temp_dict:
      temp_string_to_add += temp_dict[key]
    
    # remove the last '&' from the url-string
    string_to_add = temp_string_to_add[:-1]
    
    # create full url-string
    greyhound_server = getGreyhoundServer()
    server_to_call = '{}{}/hierarchy?{}'.format(greyhound_server[:-1], prefix_resource, string_to_add)
    print(server_to_call)

    data = read(server_to_call)
    print(type(data))
    json_read = json.loads(data)
    json_write = json.dumps(json_read)

    resp = app.response_class(response=json_write, status=200, mimetype='application/json')

    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE'
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['X-powered-by'] = 'Jippe van der Maaden'
    return resp

api.add_resource(Greyhound_read, prefix_resource + '/read', endpoint='read')
api.add_resource(Greyhound_info, prefix_resource + '/info')
api.add_resource(Greyhound_hierarchy, prefix_resource + '/hierarchy', endpoint='hierarcy')

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=5000, debug=True)
