import urllib3
import sys
import json

from flask import Flask
from flask_restful import Resource, Api, reqparse

sys.path.insert(0, '/home/ec2-user/thesis')

from util.utils import *

app = Flask(__name__)
api = Api(app)

prefix_resource = '/resource/tu-delft-campus'
greyhoud_server = getGreyhoundServer()

def read(url):
    http = urllib3.PoolManager()
    u = http.request('GET', url)
    data = u.data
    return data

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
    parser.add_argument('filter', type=str)
    parser.add_argument('schema', type=str)
    parser.add_argument('compress', type=str)
    
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
    server_to_call = '{}{}/read?{}'.format(greyhound_server[:-1], prefix_resource, string_to_add)
    
    # call greyhound server
    to_return = read(server_to_call)
    
    return to_return
    return read(server_to_call)
    return server_to_call
    return temp_dict
    return 'im reading this, will forward it to {}'.format(server_to_call)

class Greyhound_info(Resource):
  def get(self):
    # create full url-string
    greyhound_server = getGreyhoundServer()
    server_to_call = '{}{}/info'.format(greyhound_server[:-1], prefix_resource)
    json_read = json.loads(read(server_to_call))
    return json_read

class Greyhound_hierarchy(Resource):
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
    server_to_call = '{}{}/read?{}'.format(greyhound_server[:-1], prefix_resource, string_to_add)
    
    print server_to_call
    
    return read(server_to_call)
    
    json_read = json.loads(read(server_to_call))
    return json_read

api.add_resource(Greyhound_read, prefix_resource + '/read', endpoint='read')
api.add_resource(Greyhound_info, prefix_resource + '/info')
api.add_resource(Greyhound_hierarchy, prefix_resource + '/hierarchy', endpoint='hierarcy')

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=8080, debug=True)
