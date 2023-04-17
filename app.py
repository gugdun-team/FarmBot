from flask import Flask, request
from flask_restful import Api, Resource
from uuid import uuid4
import v2.chat

app = Flask(__name__)
api = Api(app)

class HelloWorld(Resource):
    def get(self):
        return {'message': 'Hello, World!'}

class Prompt(Resource):
    def get(self):
        message = request.args.get('message')
        response = v2.chat.on_message(message)
        return {
            'result': 'success',
            'data': {
                'id': uuid4().hex,
                'prompt': message,
                'response': response
            }
        }

api.add_resource(HelloWorld, '/')
api.add_resource(Prompt, '/prompt')

if __name__ == '__main__':
    app.run(debug=False)