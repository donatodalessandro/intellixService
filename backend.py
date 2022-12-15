import os
import random
import string
import time
import uuid
from bson import json_util
from intelxapi import intelx
from flask import Flask, jsonify, request
import json
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from paho.mqtt.client import Client
from dateutil import parser

# Importazione del modulo di PyMongo
import pymongo

# mqttBroker ="mqtt.eclipseprojects.io"
from models import SeachScheduleResponse
from mongo_class import creazioneDB

mqttBroker = "test.mosquitto.org"
app = Flask(__name__)

intelx = intelx('bb54ee22-7c93-4d94-ad58-71d39a8dca32')  # possibile ciclo con varie keys


def research_on_intelix(query, fromDate, toDate):
    format = "%Y-%m-%d"

    if (fromDate and toDate) is not None:
        results = intelx.search(query, datefrom=fromDate.strftime(format), dateto=toDate.strftime(format))  # aggiungere dei parametri
    elif (fromDate and toDate) is None:
        results = intelx.search(query)
    elif (fromDate is not None) and (toDate is None):
        results = intelx.search(query, datefrom=fromDate.strftime(format), dateto=None)
    elif (fromDate is None) and (toDate is not None):
        results = intelx.search(query, datefrom=None, dateto=toDate.strftime(format))

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
                    print(record["date"])
                    datetime_object = parser.parse(record[key])
                    print(datetime_object)
                    dizionario[key] = datetime_object.timestamp()
                    print(datetime_object.timestamp())
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
        print(nested)
        # queryDict["query"] = domain
        # queryNested.append(queryDict)
        # queryDb(queryNested)

        dict_response = {}
        dict_response["id"] = uuid.uuid4()
        dict_response["query"] = query
        dict_response["timestamp"] = time.time()
        dict_response["results"] = nested
        # creazioneDB(nested)        #  la si aggiunge quando dobbiamo attivare lo scheduler
        return dict_response, 200  # SearchScheduleResponseDTO

    except Exception as e:
        error = {'Error': 'Internal Server Error'}
        return error, 500


def research_on_intelix_query(query):
    format = "%Y-%m-%d"

    results = intelx.search(query)  # aggiungere dei parametri
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
                    dizionario[key] = datetime_object.timestamp()
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
        # print(nested)
        # queryDict["query"] = domain
        # queryNested.append(queryDict)
        # queryDb(queryNested)

        dict_response = {}
        dict_response["id"] = uuid.uuid4()
        dict_response["query"] = query
        dict_response["timestamp"] = time.time()
        dict_response["results"] = nested
        # creazioneDB(nested)        #  la si aggiunge quando dobbiamo attivare lo scheduler
        return dict_response  # SearchScheduleResponseDTO

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


def tick():
    print('Tick! The time is: %s' % datetime.now())


def research_scheduler(query):
    connessione = pymongo.MongoClient("mongodb://localhost:27017/")

    # Creazione del database   --- Cambiare nome alla collezione
    database = connessione["IntelX"]
    collection_results = database["results"]
    collection_schedulers = database["schedulers"]

    # Limitare i risultati da estrarre
    criterio = {"query": query}
    selezione = collection_schedulers.find(criterio)
    jstr = parse_json(selezione)

    if jstr != []:

        dict_response = {}
        dict_response["id"] = uuid.uuid4()
        dict_response["query"] = query
        dict_response["timestamp"] = time.time()
        dict_response["results"] = research_on_db(query)

        return dict_response
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

    result_dict = research_on_intelix_query(query)
    query_list = []

    '''
    # Estrazione dei documenti di una collection
    for selezione in nuovacollection.find():
        for elem in lista:
            if elem['query'] == selezione['query']:
                lista.remove(elem)
    '''
    dizionario = {}
    dizionario["query"] = query
    query_list.append(dizionario)
    schedulers.insert_many(query_list)
    # print(result_dict["results"])
    results.insert_many(result_dict["results"])

    return result_dict


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

    format = "%Y-%m-%d"
    criterio_query = {"query": query}
    criterio_fromDate = {"date": {'$gte': fromDate}}
    criterio_toDate = {"date": {'$lte': toDate}}

    if (fromDate and toDate) is not None:
        selezione = nuovacollection.find({'$and': [criterio_query, criterio_fromDate, criterio_toDate]})
    elif (fromDate and toDate) is None:
        selezione = nuovacollection.find(criterio_query)
    elif (fromDate is not None) and (toDate is None):
        selezione = nuovacollection.find({'$and': [criterio_query, criterio_fromDate]})
    elif (fromDate is None) and (toDate is not None):
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
