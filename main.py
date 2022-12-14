from flask import Flask, request
import jsonpickle
from models import *

app = Flask(__name__)

basepath = "/unisannio/DWM/intelx"

@app.route(basepath + '/searches', methods=['GET'])
def search():
    searchCommand = SearchCommand(request.json)

    ##METODO GET

    print(searchCommand)



    response = SeachScheduleResponse()
    response.id = 'test'
    response.timestamp = 11111111
    response.query = "pippo"

    result = []

    searchresult1 = SearchResult()
    searchresult1.id = 'test2'
    searchresult1.name = 'pippo.txt'

    searchresult2 = SearchResult()
    searchresult2.id = 'test5'
    searchresult2.name = 'pipp4o.txt'

    result.append(searchresult1)
    result.append(searchresult2)

    response.result = result

    print(response)
    return jsonpickle.encode(response, unpicklable=False)



@app.route(basepath + '/schedulers', methods=['POST', 'DELETE'])
def schedule():
    scheduleCommand = ScheduleCommand(request.json)
    if(request.method == 'POST'):
        return #METODO DI GESTIONE POST
    if (request.method == 'DELETE'):
        return #METODO DI GESTIONE DELETE



if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    app.run()
