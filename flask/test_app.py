from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

class Quotes(Resource):
  def get(self):
      return {
          'ataturk': {'quote': ['A 1', 'A 2', 'A 3']},
          'linus': {'quote': ['Talk is cheap. Show me the code.']}
          }

api.add_resource(Quotes, '/')

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=80, debug=True)
