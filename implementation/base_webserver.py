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

prefix_resource = 'municipality-delft'
greyhoud_server = getGreyhoundServer()


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
    
    param_dict = parser.parse_args()
    
    # remove arguments not in the original query
    remove_args = []
    for key in param_dict:
      if param_dict[key] == None:
        remove_args.append(key)
    for key in remove_args:
      del param_dict[key]

    filename = '{} {} {}.las'.format(param_dict['depthBegin'], param_dict['depthEnd'], param_dict['bounds'])

    r = GreyhoundConnection(prefix_resource, param_dict, filename)
    r.get_pointcloud(param_dict)

    # fake response, so the speck.ly front-end will keep sending requests
    resp = make_response(send_file(io.BytesIO(data), attachment_filename='read', mimetype='binary/octet-stream'))
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE'
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['Connection'] = 'keep-alive'
    resp.headers['X-powered-by'] = 'Jippe van der Maaden'
    return resp


class Greyhound_info(Resource):
  def get(self):
    # create full url-string
    greyhound_server = getGreyhoundServer()

    r = GreyhoundConnection(prefix_resource)
    data = r.info()

    print(data)
#    json_read = json.loads(data)
#    print(json_read)
    json_write = json.dumps(data)
    print(json_write)

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

api.add_resource(Greyhound_read, '/resource/' + prefix_resource + '/read', endpoint='read')
api.add_resource(Greyhound_info, '/resource/' + prefix_resource + '/info')
api.add_resource(Greyhound_hierarchy, '/resource/' +  prefix_resource + '/hierarchy', endpoint='hierarcy')

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=5000, debug=True)
