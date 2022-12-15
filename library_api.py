from asyncio_mqtt import Client
from cheroot import wsgi
from intelxapi import intelx
from datetime import datetime
from flask import Flask, request
import re
from backend import research_scheduler, research_on_intelix, research_on_db, research_on_db_by_date, regular_dot
from models import SearchCommand, SeachScheduleResponse, ScheduleCommand
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




@scheduler.task('interval', id='scheduler_job', seconds=updateIntervalSec, misfire_grace_time=900)
def job():
    messaggio = "test message"

    mqtt.publish(topic, messaggio, qos=1)
    print("Done")


intelx = intelx('6dc578ec-490b-49d5-8717-6379a2118895')  # possibile ciclo con varie keys


@app.get(basepath+'/searches')
def researchByDomain():
    """
        Endpoint Rest per la ricerca di un dominio mediante l'API di Intellix

        :param domain: Il nome del dominio da cercare
        :return: Lista contenete i dump in formato json

    """

    searchCommand = SearchCommand(request.json)

    query = searchCommand.query
    fromDate = None
    toDate = None

    if searchCommand.fromDate is not None: fromDate = datetime.fromtimestamp(searchCommand.fromDate)
    if searchCommand.toDate is not None: toDate = datetime.fromtimestamp(searchCommand.toDate)

    # controlla se sul db ho già elementi per quella query
    # se si li restituisco come SearchScheduleResponseDTO
    # altrimenti ricerca su intellix che restituisce come SearchScheduleResponseDTO MA NON SALVA SUL DB

    results = research_on_db_by_date(query, searchCommand.fromDate, searchCommand.toDate)

    if results != []:

        dict_response = {}
        dict_response["id"] = uuid.uuid4().hex
        dict_response["query"] = query
        dict_response["timestamp"] = int(re.search("\d+", str(time.time())).group())
        dict_response["results"] = results

        return dict_response
    else:
        # print(fromDate)
        format = "%Y-%m-%d"
        # print(datetime.now().strftime(format))
        # print(datetime.fromtimestamp(int(re.search("\d+", str(time.time())).group())).strftime(format))
        return research_on_intelix(query, fromDate, toDate)


'''
@app.get('/unisannio/DWM/intelx/searches')
def research():

    """
        Endpoint Rest per la ricerca di un dominio e di un numero n di risultati medianti query param

        :return: Lista contenete i dump in formato json

    """

    query = request.args['query']
    maxResults = int(request.args['maxresults'])

    return stampaHTMLquery(query, maxResults)

def stampaHTMLquery(query, maxResults):
    connessione = pymongo.MongoClient("mongodb://localhost:27017/")

    # Creazione del database
    database = connessione["IntelX"]
    nuovacollection = database["results"]

    results = {}

    # Limitare i risultati da estrarre
    criterio = {"query": query}
    selezione = nuovacollection.find(criterio).limit(maxResults)

    jstr = parse_json(selezione)

    return jsonify(jstr)

'''


@app.route(basepath+'/schedulers', methods=['POST', 'DELETE'])
def schedulers():
    """
        Endpoint Rest per l'attivazione dell'alert per verificare la presenza di un nuovo dump

        :return: Lista contenete i dump in formato json

    """
    # estraiamo il parametro dal body

    scheduleCommand = ScheduleCommand(request.json)
    query = scheduleCommand.query

    if request.method == 'POST':
        return research_scheduler(query)
    else:
        return drop_collection(query)


'''
    #cosa ci passano?
    #query = request.form.args['query']
    query = request.get_json()
    print(query)
    return research_alert(query)
'''

if __name__ == '__main__':

    addr = '0.0.0.0', 5002
    server = wsgi.Server(addr, app)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print("-----------------Debug message: server stopped")

'''
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(tick, 'interval', seconds=15)
        scheduler.start()
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()
        print("-----------------Debug message: server stopped")
'''
