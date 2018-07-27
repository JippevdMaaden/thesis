from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

prefix_resource = '/resource/tu-delft-campus'

class Greyhound(Resource):
  def get(self):
    return 'im reading this'

api.add_resource(Greyhound, prefix_resource + '/read')


if __name__ == '__main__':
  app.run(host="0.0.0.0", port=80, debug=True)
