from cheroot import wsgi
from datetime import datetime
from flask import Flask, request
import re
import backend
from models import SearchCommand, ScheduleCommand, TokenCommand
import time
import uuid
from flask_apscheduler import APScheduler
from flask_mqtt import Mqtt
import config


class Config:
    SCHEDULER_API_ENABLED=True
    MQTT_BROKER_URL = config.mqttBroker
    MQTT_BROKER_PORT = config.mqttBrokerPort
    MQTT_REFRESH_TIME = 1.0


app = Flask(__name__)
app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
mqtt = Mqtt(app)


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    """
        Funzione di debug che permette di verificare l'effettiva connessione al broker mqtt

    """
    print("Connesso")

@app.route(config.basepath+'/token', methods=['PUT','GET'])
def set_token():
    """
        Funzione che permette di settare il token mediante il metodo PUT o acquisirlo mediante il metodo GET

        :return: in base al tipo di metodo Http il token verrà settato o ritornato come json

    """

    if request.method == 'PUT':
        tokenCommand = TokenCommand(request.json)
        backend.set_token(tokenCommand.token)
        return {}
    else:
        return {"token": backend.get_token()}


@app.post(config.basepath+'/searches')
def research_by_domain():

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

@app.route(config.basepath+'/schedulers', methods=['POST'])
def research_schedulers():
    """
        Endpoint Rest per l'attivazione dell'alert per verificare la presenza di un nuovo dump

        :return: Lista contenete i dump in formato json

    """

    scheduleCommand = ScheduleCommand(request.json)
    query = scheduleCommand.query
    return backend.research_scheduler(query)

@app.route(config.basepath+'/schedulers/<query>', methods=['DELETE'])
def delete_schedulers(query):
    """
        Funzione che permette di eliminare dalla collezione nel database lo scheduler associato alla query

        :param query: scheduler da eliminare
        :return:

    """
    return backend.drop_collection(query)



@app.get(config.basepath+'/searches/<query>')
def last_results_from_query(query):

    """
        Funzione che ritorna i risultati della ricerca per query sul database

        :return: DTO contenente i risultati della ricerca su db

    """
    return backend.DTO_creation(query, backend.research_on_db(query))


if __name__ == '__main__':
    addr = '0.0.0.0', 5002
    server = wsgi.Server(addr, app)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print("-----------------Debug message: server stopped")
