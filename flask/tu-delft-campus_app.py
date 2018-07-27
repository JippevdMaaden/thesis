import urllib3
import sys

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
    
    remove_args = []
    for key in temp_dict:
      if temp_dict[key] == None:
        remove_args.append(key)
    
    for key in remove_args:
      del temp_dict[key]
    
    for key in temp_dict:
      if key == 'schema':
        temp_var = temp_dict[key]
        temp_var.replace("/", "")
        temp_dict[key] = temp_var
      new_var = key+ '=' + temp_dict[key] + '&'
      temp_dict[key] = new_var
    
    temp_string_to_add = ''
    for key in temp_dict:
      temp_string_to_add += temp_dict[key]
    
    string_to_add = temp_string_to_add[:-1]
    
    greyhound_server = getGreyhoundServer()
    server_to_call = '{}{}/read?{}'.format(greyhound_server[:-1], prefix_resource, string_to_add)
    
    #return read(server_to_call)
    return server_to_call
    return temp_dict
    return 'im reading this, will forward it to {}'.format(server_to_call)

class Greyhound_info(Resource):
  def get(self):
    return 'im reading this info'

api.add_resource(Greyhound_read, prefix_resource + '/read', endpoint='read')
api.add_resource(Greyhound_info, prefix_resource + '/info')

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=8080, debug=True)
