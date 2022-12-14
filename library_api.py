import os
import time
from bson import json_util
from intelxapi import intelx
from flask import Flask, jsonify, request
import json
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from paho.mqtt.client import Client

# Importazione del modulo di PyMongo
import pymongo

#mqttBroker ="mqtt.eclipseprojects.io"
mqttBroker = "test.mosquitto.org"
app = Flask(__name__)

intelx = intelx('3f2ef7d9-d6a2-4ce6-991e-254e2ae0d090')  # possibile ciclo con varie keys

@app.get('/unisannio/DWM/intelx/searches/<domain>')
def researchByDomain(domain):

    """
        Endpoint Rest per la ricerca di un dominio mediante l'API di Intellix

        :param domain: Il nome del dominio da cercare
        :return: Lista contenete i dump in formato json

    """

    return stampaHTML(domain)

def stampaHTML(domain):

    results = intelx.search(domain)
    keys = ['query', 'name', 'date', 'typeh', 'bucketh']


    nested = []
    jsonDict = {}
    #queryNested = []
    #queryDict = {}


    try:
        for record in results["records"]:
            dizionario = {}
            for key in keys:
                if key == 'query':
                    dizionario['query'] = domain
                else:
                    dizionario[key] = record[key]
            #print(dizionario)
            nested.append(dizionario)
            jsonDict[record["name"]] = dizionario

        print("******************************")
        #print(nested)

        jstr = parse_json(jsonDict)
        #json.dumps(jsonDict, indent=4)

        #queryDict["query"] = domain
        #queryNested.append(queryDict)

        creazioneDB(nested)
        #queryDb(queryNested)
        return jsonify(jstr), 200

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




def creazioneDB(lista):
    connessione = pymongo.MongoClient("mongodb://localhost:27017/")

    # Creazione del database
    database = connessione["IntelX"]
    nuovacollection = database["results"]

    # Estrazione dei documenti di una collection
    for selezione in nuovacollection.find():
        for elem in lista:
            if elem['name'] == selezione['name']:
                lista.remove(elem)
    nuovacollection.insert_many(lista)
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

def parse_json(data):
    return json.loads(json_util.dumps(data))

def tick():
    print('Tick! The time is: %s' % datetime.now())


@app.get('/unisannio/DWM/intelx/schedulers')
def schedulers():
    """
        Endpoint Rest per l'attivazione dell'alert per verificare la presenza di un nuovo dump

        :return: Lista contenete i dump in formato json

    """
    #cosa ci passano?
    #query = request.form.args['query']
    query = request.get_json()
    print(query)
    return research_alert(query)

def research_alert(query):

    connessione = pymongo.MongoClient("mongodb://localhost:27017/")

    # Creazione del database   --- Cambiare nome alla collezione
    database = connessione["IntelX"]
    collection_results = database["results"]
    collection_alert = database["alert"]

    # Limitare i risultati da estrarre
    criterio = {"query": query}
    selezione = collection_alert.find(criterio)
    jstr = parse_json(selezione)

    if jstr != []:
        return "Alert già presente"
    else:
        create_alert(query)

def create_alert(query):

    add_alert_db(query)
    publish_topic(query)

def add_alert_db(query):

    connessione = pymongo.MongoClient("mongodb://localhost:27017/")
    # Creazione del database
    database = connessione["IntelX"]
    #collection_results = database["results"]
    nuovacollection = database["alerts"]

    query_list = []

    '''
    # Estrazione dei documenti di una collection
    for selezione in nuovacollection.find():
        for elem in lista:
            if elem['query'] == selezione['query']:
                lista.remove(elem)
    '''

    query_list.append(query)
    nuovacollection.insert_many(query_list)

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

    json_response = {"Valore" : "Funziona"}
    print("send dumps")
    return jsonify(json_response)

'''
if __name__ == '__main__':

    addr = '127.0.0.1', 5000
    server = wsgi.Server(addr, app)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print("-----------------Debug message: server stopped")
'''
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