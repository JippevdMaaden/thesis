from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

class Hello_world(Resource):
  def get(self):
    return 'Hello world'

class Quotes(Resource):
  def get(self):
      return {
          'ataturk': {'quote': ['A 1', 'A 2', 'A 3']},
          'linus': {'quote': ['Talk is cheap. Show me the code.']}
          }

class Info(Resource):
  def get(self):
    return 'info query'
  
class Read(Resource):
  def get(self):
    return 'read query'
  
class Static(Resource):
  def get(self):
    return 'static query'
  
class Count(Resource):
  def get(self):
    return 'count query'

class Hierarchy(Resource):
  def get(self):
    return 'hierarchy query'
  
class Files(Resource):
  def get(self):
    return 'files query'
  

    
api.add_resource(Hello_world, '/')
api.add_resource(Quotes, '/quotes')

api.add_resource(Info, '/info')
api.add_resource(Read, '/read')
#api.add_resource(Static, '/static')
#api.add_resource(Count, '/count')
#api.add_resource(Hierarchy, '/hierarchy')
#api.add_resource(Files, '/files')

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=80, debug=True)
