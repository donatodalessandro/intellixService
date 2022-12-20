import os
import random
import string
import re
import time
import uuid
from itertools import count
from flask_apscheduler import APScheduler
from flask_mqtt import Mqtt
from bson import json_util
from intelxapi import intelx
from flask import Flask, jsonify, request
import json
from datetime import datetime
from paho.mqtt.client import Client
from dateutil import parser

# Importazione del modulo di PyMongo
import pymongo

# mqttBroker ="mqtt.eclipseprojects.io"
import library_api
from models import SeachScheduleResponse
from mongo_class import creazioneDB


basepath = "/unisannio/DWM/intelx"
mqttBroker = "test.mosquitto.org"
clientID = "Sub_test"
topic = "unisannio/DWM/intelx/alert"
updateIntervalSec = 120
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

intelx = intelx('6dc578ec-490b-49d5-8717-6379a2118895')  # possibile ciclo con varie keys


def research_on_intelix(query, fromDate, toDate):
    format = "%Y-%m-%d %H:%M:%S"

    if fromDate is not None and toDate is not None:
        results = intelx.search(query, datefrom=fromDate.strftime(format), dateto=toDate.strftime(format), maxresults=1000000000)  # aggiungere dei parametri
    elif fromDate is None and toDate is None:
        results = intelx.search(query, maxresults=1000000000)
    elif (fromDate is not None) and (toDate is None):
        print(datetime.now().strftime(format))
        results = intelx.search(query, datefrom=fromDate.strftime(format), dateto=datetime.now().strftime(format), maxresults=1000000000)
    elif (fromDate is None) and (toDate is not None):
        fromD= datetime.fromtimestamp(0)
        print(fromD.strftime(format))
        results = intelx.search(query, datefrom= fromD.strftime(format), dateto=toDate.strftime(format), maxresults=1000000000)

    keys = ['_id', 'query', 'name', 'date', 'typeh', 'bucketh']

    nested = []
    jsonDict = {}

    datetime_str = "2022-12-13T00:24:30.98013Z"

    try:
        for record in results["records"]:
            dizionario = {}
            for key in keys:
                if key == 'query':
                    dizionario['query'] = query
                elif key == 'date':
                    datetime_object = parser.parse(record[key])
                    dizionario[key] = regular_dot(datetime_object)
                elif key == '_id':
                    dizionario['_id'] = uuid.uuid4().hex
                else:
                    dizionario[key] = record[key]
            # print(dizionario)
            nested.append(dizionario)
            jsonDict[record["name"]] = dizionario

        print("******************************")
        # print(nested)
        jstr = parse_json(jsonDict)
        # json.dumps(jsonDict, indent=4)
        # queryDict["query"] = domain
        # queryNested.append(queryDict)
        # queryDb(queryNested)

        '''
        dict_response = {}
        dict_response["id"] = uuid.uuid4()
        dict_response["query"] = query
        dict_response["timestamp"] = int(re.search("\d+", str(time.time())).group())
        dict_response["results"] = nested
        
        # creazioneDB(nested)        #  la si aggiunge quando dobbiamo attivare lo scheduler
        return dict_response, 200  # SearchScheduleResponseDTO
        '''

        return DTO_creation(query, nested)

    except Exception as e:
        error = {'Error': 'Internal Server Error'}
        return error, 500


def research_on_intelix_query(query):
    format = "%Y-%m-%d"

    results = intelx.search(query,maxresults=1000000000)  # aggiungere dei parametri
    keys = ['_id', 'query', 'name', 'date', 'typeh', 'bucketh']

    nested = []
    jsonDict = {}
    # queryNested = []
    # queryDict = {}

    datetime_str = "2022-12-13T00:24:30.98013Z"

    try:
        for record in results["records"]:
            dizionario = {}
            for key in keys:
                if key == 'query':
                    dizionario['query'] = query
                elif key == 'date':
                    datetime_object = parser.parse(record[key])
                    dizionario[key] = regular_dot(datetime_object)
                elif key == '_id':
                    dizionario['_id'] = uuid.uuid4().hex
                else:
                    dizionario[key] = record[key]
            # print(dizionario)
            nested.append(dizionario)
            jsonDict[record["name"]] = dizionario

        print("******************************")
        jstr = parse_json(jsonDict)
        # json.dumps(jsonDict, indent=4)
        # print(nested)
        # queryDict["query"] = domain
        # queryNested.append(queryDict)
        # queryDb(queryNested)

        '''
        dict_response = {}
        dict_response["id"] = uuid.uuid4()
        dict_response["query"] = query
        dict_response["timestamp"] = int(re.search("\d+", str(time.time())).group())
        dict_response["results"] = nested
        # creazioneDB(nested)        #  la si aggiunge quando dobbiamo attivare lo scheduler
        return dict_response  # SearchScheduleResponseDTO
        '''

        return DTO_creation(query, nested)

    except Exception as e:
        error = {'Error': 'Internal Server Error'}
        return error, 500


'''
data = {"system_id": ,
        "timestamp": ,
        "query": domain,
        "result": nested
        }
'''


def parse_json(data):
    return json.loads(json_util.dumps(data))



def research_scheduler(query):
    connessione = pymongo.MongoClient(library_api.mongoHost)

    # Creazione del database   --- Cambiare nome alla collezione
    database = connessione["IntelX"]
    collection_results = database["results"]
    collection_schedulers = database["schedulers"]

    # Limitare i risultati da estrarre
    criterio = {"query": query}
    selezione = collection_schedulers.find(criterio)
    jstr = parse_json(selezione)

    if jstr != []:

        '''
        dict_response = {}
        dict_response["id"] = uuid.uuid4()
        dict_response["query"] = query
        dict_response["timestamp"] = int(re.search("\d+", str(time.time())).group())
        dict_response["results"] = research_on_db(query)

        return dict_response
        '''

        return DTO_creation(query, research_on_db(query))

    else:
        return create_scheduler(query)


def create_scheduler(query):
    return add_scheduler_to_db(query)
    # publish_topic(query)


def add_scheduler_to_db(query):
    connessione = pymongo.MongoClient("mongodb://localhost:27017/")
    # Creazione del database
    database = connessione["IntelX"]
    results = database["results"]
    schedulers = database["schedulers"]

    #scheduler deve essere creato

    query_list = []
    dizionario = {}
    dizionario["query"] = query
    query_list.append(dizionario)
    schedulers.insert_many(query_list)

    scheduler.add_job(query,lambda: research_intelix_scheduler(query))

    return {}
    # result_dict = research_on_intelix_query(query)
    # query_list = []
    #
    # '''
    # # Estrazione dei documenti di una collection
    # for selezione in nuovacollection.find():
    #     for elem in lista:
    #         if elem['query'] == selezione['query']:
    #             lista.remove(elem)
    # '''
    # dizionario = {}
    # dizionario["query"] = query
    # query_list.append(dizionario)
    # schedulers.insert_many(query_list)
    # # print(result_dict["results"])
    # results.insert_many(result_dict["results"])
    #
    # return result_dict


@scheduler.task('interval', id='scheduler_job', seconds=updateIntervalSec, misfire_grace_time=900)
def job():
    connessione = pymongo.MongoClient("mongodb://localhost:27017/")
    # Creazione del database
    database = connessione["IntelX"]
    results = database["results"]
    schedulers = database["schedulers"].find()

    try:
        while True:
            scheduler = schedulers.next()
            research_intelix_scheduler(scheduler["query"])

    except StopIteration:
       print("fine")


    # messaggio = "test message"
    # mqtt.publish(topic, messaggio, qos=1)
    print("Done")


def research_intelix_scheduler(query) :
    print("entrato nella funzione per la query "+query)
    #deve andare sul db
    connessione = pymongo.MongoClient("mongodb://localhost:27017/")
    # Creazione del database
    database = connessione["IntelX"]
    results = database["results"]
    schedulers = database["schedulers"]

    # filtrare per query
    criterio = {"query": query}
    # prendere i risultati per quella query
    cursore = results.find(criterio)

    #selezione = results.find(criterio).sort("date",-1)

    try:
        selezione = cursore.next()
        print("Ricerca su intelix sull data "+ str(datetime.fromtimestamp(selezione["date"])) + "per la query "+ query)
        dto = research_on_intelix(query, datetime.fromtimestamp(selezione["date"]), None)
    except StopIteration:
        dto = research_on_intelix_query(query)
        print("Ricerca su intelix per la query " + query)

    if len(dto["results"]) >0:
        results.insert_many(dto["results"])

    return {}


def publish_topic(topic):
    print("metodo publish")
    async_scheduler(topic)


def async_scheduler(query):
    print("metodo async_scheduler")
    research_new_dump(query)
    '''
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(research_new_dump(query), 'interval', seconds=15)
        scheduler.start()
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()
        print("-----------------Debug message: server stopped")
    '''


def research_new_dump(query):
    print("metodo research dumps")

    dumps, status_code = stampaHTML(query["query"])

    print(dumps)
    print(status_code)

    if status_code == 200:
        message = "Sono presenti nuovi dumps"
        send_dumps(message)
        print("funonzia")
    else:
        message = "Non sono presenti nuovi dumps"
        send_dumps(message)


def send_dumps(result_query):
    def on_publish(client, userdata, mid):
        print("Messaggio pubblicato")

    client = Client("Publisher_test")
    client.on_publish = on_publish
    client.connect(mqttBroker)
    client.loop_start()
    client.publish(topic="test", payload=result_query)
    client.loop_stop()
    client.disconnect()

    json_response = {"Valore": "Funziona"}
    print("send dumps")
    return jsonify(json_response)


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
'''


def research_on_db(query):
    connessione = pymongo.MongoClient("mongodb://localhost:27017/")

    # Creazione del database
    database = connessione["IntelX"]
    nuovacollection = database["results"]

    results = {}

    # Limitare i risultati da estrarre
    criterio = {"query": query}
    selezione = nuovacollection.find(criterio)

    jstr = parse_json(selezione)  # return DTO

    return jstr


def research_on_db_by_date(query, fromDate, toDate):
    connessione = pymongo.MongoClient("mongodb://localhost:27017/")

    # Creazione del database
    database = connessione["IntelX"]
    nuovacollection = database["results"]

    results = {}

    criterio_query = {"query": query}
    criterio_fromDate = {"date": {'$gte': fromDate}}
    criterio_toDate = {"date": {'$lte': toDate}}

    if fromDate is not None and toDate is not None:
        selezione = nuovacollection.find({'$and': [criterio_query, criterio_fromDate, criterio_toDate]})
    elif fromDate is None and toDate is None:
        selezione = nuovacollection.find(criterio_query)
    elif fromDate is not None and toDate is None:
        selezione = nuovacollection.find({'$and': [criterio_query, criterio_fromDate]})
    elif fromDate is None and toDate is not None:
        selezione = nuovacollection.find({'$and': [criterio_query, criterio_toDate]})

    jstr = parse_json(selezione)  # return DTO

    print(selezione)

    return jstr


def create_db():
    dict = research_on_intelix()
    connessione = pymongo.MongoClient("mongodb://localhost:27017/")

    # Creazione del database
    database = connessione["IntelX"]
    nuovacollection = database["results"]

    results = {}

    # Limitare i risultati da estrarre
    criterio = {"query": query}
    selezione = nuovacollection.find(criterio)

    jstr = parse_json(selezione)

    return jsonify(jstr)


def regular_dot(datetime_object):
    "regular expression per eliminare il punto dal timestamp"
    date = re.search("\d+", str(datetime_object.timestamp()))
    return int(date.group())


def DTO_creation(query, list):
    dict_response = {}
    dict_response["id"] = uuid.uuid4()
    dict_response["query"] = query
    dict_response["timestamp"] = int(re.search("\d+", str(time.time())).group())
    dict_response["results"] = list

    return dict_response