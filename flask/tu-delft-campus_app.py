import sys

from flask import Flask
from flask_restful import Resource, Api, reqparse

sys.path.insert(0, '/home/ec2-user/thesis')

from util.utils import *

app = Flask(__name__)
api = Api(app)

prefix_resource = '/resource/tu-delft-campus'
greyhoud_server = getGreyhoundServer()

class Greyhound_read(Resource):
  def get(self):
    parser = reqparse.RequestParser()
    parser.add_argument('depthEnd', type=int)
    parser.add_argument('depthEnd', type=int)
    parser.add_argument('depthBegin', type=int)
    parser.add_argument('bounds', type=str)
    parser.add_argument('scale', type=float)
    parser.add_argument('offset', type=list)
    parser.add_argument('filter')
    parser.add_argument('schema')
    parser.add_argument('compress', type=str)
    
    temp_dict = parser.parse_args()
    
    remove_args = []
    for key in temp_dict:
      if temp_dict[key] == None:
        remove_args.append(key)
    
    return remove_args
    
    greyhound_server = getGreyhoundServer()
    server_to_call = greyhound_server + action
    
    return 'im reading this, will forward it to {}'.format(server_to_call)

class Greyhound_info(Resource):
  def get(self):
    return 'im reading this info'

api.add_resource(Greyhound_read, prefix_resource + '/read', endpoint='read')
api.add_resource(Greyhound_info, prefix_resource + '/info')

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=8080, debug=True)
