import sys

from flask import Flask
from flask_restful import Resource, Api

sys.path.insert(0, '/home/ec2-user/thesis')

from util.utils import *

app = Flask(__name__)
api = Api(app)

prefix_resource = '/resource/tu-delft-campus'
greyhoud_server = getGreyhoundServer()

class Greyhound_read(Resource):
  def get(self, action):
    server_to_call = greyhound_server + action
    return 'im reading this, will forward it to {}'.format(server_to_call)

class Greyhound_info(Resource):
  def get(self):
    return 'im reading this info'

api.add_resource(Greyhound_read, prefix_resource + '/read<string:action>')
api.add_resource(Greyhound_info, prefix_resource + '/info')

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=8080, debug=True)
