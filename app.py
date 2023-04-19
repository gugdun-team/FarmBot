from flask import Flask, request
from flask_restful import Api, Resource
from uuid import uuid4
import v2.chat
import threading

app = Flask(__name__)
api = Api(app)

TIMEOUT_MAX = 1000
promptQueue = []
userList = []

class User():
    def __init__(self):
        self.__id = uuid4().hex
        self.__timeout = 0
        self.out = None
        # self.out = v2.chat.load_all_stat('', 'chat_init')
    
    def getId(self):
        return self.__id
    
    def getTimeout(self):
        return self.__timeout

    def reset(self):
        self.__timeout = 0

    def tick(self):
        self.__timeout += 1

class Prompt(threading.Thread):
    def __init__(self, user, message):
        threading.Thread.__init__(self)
        self.__id = uuid4().hex
        self.__user = user
        self.__message = message
        self.__status = False
        self.__response = ['']

    def run(self):
        if (self.__user.out == None):
            self.__user.out = v2.chat.run_rnn(v2.chat.pipeline.encode(v2.chat.init_prompt))
            v2.chat.save_all_stat('', 'chat_init', self.__user.out)
            v2.chat.gc.collect()
            v2.chat.torch.cuda.empty_cache()
        v2.chat.on_message(self.__message, self.__response, self.__user.out)
        self.__status = True

    def getId(self):
        return self.__id

    def getStatus(self):
        return self.__status

    def getResponse(self):
        return "".join(self.__response)

class LoginResource(Resource):
    def get(self):
        userList.append(User())
        return {
            'user_id': userList[len(userList)-1].getId()
        }

class PromptResource(Resource):
    def get(self):
        user_id = request.args.get('user_id')
        user = [x for x in userList if x.getId() == user_id]
        if (len(user) < 1):
            return {
                'status': False
            }
        user[0].reset()
        message = request.args.get('message')
        prompt = Prompt(user[0], message)
        prompt.start()
        promptQueue.append(prompt)
        return {
            'prompt_id': prompt.getId()
        }

class ResponseResource(Resource):
    def get(self):
        prompt_id = request.args.get('prompt_id')
        prompt = [x for x in promptQueue if x.getId() == prompt_id]
        if (len(prompt) > 0):
            status = prompt[0].getStatus()
            response = prompt[0].getResponse()

            if (status == True):
                promptQueue.remove(prompt[0])

            return {
                'status': status,
                'response': response
            }
        else:
            return {
                'status': True 
            }

api.add_resource(LoginResource, '/login')
api.add_resource(PromptResource, '/prompt')
api.add_resource(ResponseResource, '/response')

if __name__ == '__main__':
    app.run(debug=False)
    def userGC():
        for user in userList:
            user.tick()
            if user.getTimeout() > TIMEOUT_MAX:
                print(f"User {user.getId()} expired")
                userList.remove(user)
        threading.Timer(1, userGC).start()
    userGC()
