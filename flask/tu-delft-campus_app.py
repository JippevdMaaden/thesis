from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

prefix_resource = '/resource/tu-delft-campus'

class Greyhound_read(Resource):
  def get(self):
    return 'im reading this'

class Greyhound_info(Resource):
  def get(self):
    return 'im reading this info'

api.add_resource(Greyhound_read, prefix_resource + '/read')
api.add_resource(Greyhound_info, prefix_resource + '/info')

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=8080, debug=True)
