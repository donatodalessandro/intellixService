from cheroot import wsgi
from datetime import datetime
from markupsafe import escape
from flask import Flask, request
import re
import backend
from models import SearchCommand, ScheduleCommand, TokenCommand
from mongo_class import drop_collection
import time
import uuid
from flask_apscheduler import APScheduler
from flask_mqtt import Mqtt


basepath = "/unisannio/DWM/intelx"
mqttBroker = "test.mosquitto.org"
clientID = "Sub_test"
topic = "unisannio/DWM/intelx/alert"
updateIntervalSec = 5
mongoHost = "mongodb://localhost:27017/"


class Config:
    SCHEDULER_API_ENABLED=True
    MQTT_BROKER_URL = mqttBroker
    MQTT_BROKER_PORT = 1883
    MQTT_REFRESH_TIME = 1.0


app = Flask(__name__)
app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
mqtt = Mqtt(app)


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("Connesso")

@app.route(basepath+'/token', methods=['PUT','GET'])
def set_token():
    if request.method == 'PUT':
        tokenCommand = TokenCommand(request.json)
        backend.set_token(tokenCommand.token)
        return {}
    else:
        return {"token": backend.get_token()}


@app.post(basepath+'/searches')
def researchByDomain():

    """
        Endpoint Rest per la ricerca di un dominio mediante l'API di Intelx

        :param domain: Il nome del dominio da cercare
        :return: Lista contenete i dump in formato json

    """

    searchCommand = SearchCommand(request.json)

    query = searchCommand.query
    fromDate = None
    toDate = None

    if searchCommand.fromDate is not None: fromDate = datetime.fromtimestamp(searchCommand.fromDate)
    if searchCommand.toDate is not None: toDate = datetime.fromtimestamp(searchCommand.toDate)

    results = backend.research_on_db_by_date(query, searchCommand.fromDate, searchCommand.toDate)

    if results != []:

        dict_response = {}
        dict_response["id"] = uuid.uuid4().hex
        dict_response["query"] = query
        dict_response["timestamp"] = int(re.search("\d+", str(time.time())).group())
        dict_response["results"] = results

        return dict_response
    else:
        format = "%Y-%m-%d"
        return backend.research_on_intelx(query, fromDate, toDate)

@app.route(basepath+'/schedulers', methods=['POST'])
def research_schedulers():
    """
        Endpoint Rest per l'attivazione dell'alert per verificare la presenza di un nuovo dump

        :return: Lista contenete i dump in formato json

    """

    scheduleCommand = ScheduleCommand(request.json)
    query = scheduleCommand.query
    return backend.research_scheduler(query)

@app.route(basepath+'/schedulers/<query>', methods=['DELETE'])
def delete_schedulers(query):
    return drop_collection(query)



@app.get(basepath+'/searches/<query>')
def last_results_from_query(query):
   return backend.DTO_creation(query, backend.research_on_db(query))

#
# if __name__ == '__main__':
#     addr = '0.0.0.0', 5002
#     server = wsgi.Server(addr, app)
#     try:
#         server.start()
#     except KeyboardInterrupt:
#         server.stop()
#         print("-----------------Debug message: server stopped")
