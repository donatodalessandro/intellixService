import re
import time
import uuid
from flask_apscheduler import APScheduler
from flask_mqtt import Mqtt
from bson import json_util
from intelxapi import intelx
import json
from datetime import datetime
from dateutil import parser
import config

# Importazione del modulo di PyMongo
import pymongo
from library_api import app


mqtt = Mqtt(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    """
        Funzione di debug che permette di verificare l'effettiva connessione al broker mqtt
    """
    if rc == 0:
       print('Connected successfully to MQTT')
    else:
       print('Bad connection. Code:', rc)


def drop_collection(query):
    """
        Funzione per effettuare il drop della collezione sul db
        :param query: nome della collezione da eliminare
    """
    connessione = pymongo.MongoClient(config.mongoHost)
    # Creazione del database
    database = connessione["IntelX"]
    results_collection = database["results"]
    schedulers_collection = database["schedulers"]
    # Rimuovere dati da una collection
    criterio = {"query": query}
    results_collection.delete_many(criterio)
    schedulers_collection.delete_many(criterio)
    print("Scheduler per "+query+" eliminato")
    dict_response = {}
    dict_response["message"] = "Scheduler per "+query+" eliminato"
    connessione.close()
    return dict_response

def get_token_from_db():
    """
        Funzione per il prelievo del Token Intelx dal database
        :param
        :return: Token or empty string

    """
    connessione = pymongo.MongoClient(config.mongoHost)
    database = connessione["IntelX"]
    tokens = database["tokens"]

    if tokens != []:

        cursore = tokens.find()

        try:
            token = cursore.next()
            return token["token"]

        except StopIteration:
            print("")
    else:
        return ""


my_token = get_token_from_db()
intelx_client = intelx(my_token)


def add_token_on_db(token):
    """
        Funzione per l'aggiunta del token al database

        :param token: token da aggiungere al database
        :return:

    """

    connessione = pymongo.MongoClient(config.mongoHost)
    database = connessione["IntelX"]
    tokens = database["tokens"]

    tokens.delete_many({})
    tokens.insert_one({"token": token})


def set_token(token):
    """
       Funzione per settare il valore del token da utilizzare per prelevare le informazioni da intelx

       :param token: token da settare
       :return:

   """

    global intelx_client
    intelx_client = intelx(token)
    global my_token
    my_token = token
    add_token_on_db(token)

def get_token():
    """
        Funzione che restituisce il token utilizzato per la ricerca su intelx
        :param
        :return my_token: token utilizzato per la ricerca

    """
    global my_token
    return my_token



def research_on_intelx(query, fromDate, toDate, sorter=2):
    """
        Funzione che permette di effettuare una ricerca su intelx utilizzando una query e una data di inizio e di fine

        :param query, fromDate, toDate: query di ricerca, data di inizio, data di fine
        :return DTO_creation: DTO relativo ad una ricerca su intelx

    """

    format = "%Y-%m-%d %H:%M:%S"

    if fromDate is not None and toDate is not None:
        results = intelx_client.search(query, datefrom=fromDate.strftime(format), dateto=toDate.strftime(format), maxresults=1000000000, media=24)  # aggiungere dei parametri
    elif fromDate is None and toDate is None:
        results = intelx_client.search(query, maxresults=1000000000, sort=sorter, media=24)
    elif (fromDate is not None) and (toDate is None):
        print("Ricerca da "+fromDate.strftime(format)+" a "+datetime.now().strftime(format))
        results = intelx_client.search(query, datefrom=fromDate.strftime(format), dateto=datetime.now().strftime(format), maxresults=1000000000, media=24)
    elif (fromDate is None) and (toDate is not None):
        fromD = datetime.fromtimestamp(0)
        results = intelx_client.search(query, datefrom=fromD.strftime(format), dateto=toDate.strftime(format), maxresults=1000000000, media=24)


    keys = ['_id', 'query', 'name', 'date', 'typeh', 'bucketh']

    nested = []

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
            

            if  dizionario["date"]<int(datetime.now().timestamp()): 
                nested.append(dizionario)         
        return DTO_creation(query, nested)

    except Exception as e:
        print(e)
        error = {'Error': 'Internal Server Error'}
        return error, 500


def parse_json(data):
    """
      Funzione per effettuare il parse in json

      :param data: data da parsare
      :return dato parsato

   """

    return json.loads(json_util.dumps(data))


def research_scheduler(query):
    """
       Funzione per ricercare la presenza di uno scheduler all'interno del database

       :param query: scheduler da ricercare sul db
       :return DTO, create_scheduler(query): DTO relativo alla ricerca per quella query, aggiunta del nuovo scheduler
                                             sul db

    """
    connessione = pymongo.MongoClient(config.mongoHost)

    database = connessione["IntelX"]
    collection_results = database["results"]
    collection_schedulers = database["schedulers"]

    criterio = {"query": query}
    selezione = collection_schedulers.find(criterio)
    jstr = parse_json(selezione)

    if jstr != []:
        print("Esiste già uno scheduler per la query "+query)
        return DTO_creation(query, research_on_db(query))

    else:
        print("Creazione scheduler per la query "+query)
        return add_scheduler_to_db(query)

def add_scheduler_to_db(query):
    """
      Funzione di aggiunta dello scheduler al db

      :param query: scheduler da aggiungere al db
      :return

    """
    connessione = pymongo.MongoClient(config.mongoHost)

    database = connessione["IntelX"]
    results = database["results"]
    schedulers = database["schedulers"]

    query_list = []
    dizionario = {}
    dizionario["query"] = query
    query_list.append(dizionario)
    schedulers.insert_many(query_list)
    print("Scheduler aggiunto al database per la query "+query)
    return {}


@scheduler.task('interval', id='scheduler_job', seconds=config.updateIntervalSec, misfire_grace_time=900)
def job():
    """
      Funzione che viene richiamata ad intervallo prefissato che permette di andare a effettuare la ricerca su intelx
      per quel determinato scheduler

      :param
      :return

    """
    connessione = pymongo.MongoClient(config.mongoHost)
    # Creazione del database
    database = connessione["IntelX"]
    results = database["results"]
    schedulers = database["schedulers"].find()

    try:
        print("Inizio iterazione delle query registrate")
        while True:
            scheduler = schedulers.next()
            id = research_intelx_scheduler(scheduler["query"])
            if id is not None:
                query_json = json.dumps({"query": scheduler["query"], "id": id})
                print("Invio alert su MQTT")
                result = mqtt.publish(config.topic+scheduler["query"], query_json)
                if result[0] == 0 : 
                    print("Messaggio inviato")
                else:
                    print("Non connesso a MQTT")
    except StopIteration:
        print("Fine iterazione")


def research_intelx_scheduler(query):


    """
      Funzione che permette di effettuare la ricerca su intelx utilizzando lo scheduler passato come argomento

      :param query: scheduler per la ricerca su intelx
      :return recente[_id]: ritorna la ricerca più recente per quello scheduler

    """
    print("Entrato nella funzione per la query " + query)

    connessione = pymongo.MongoClient(config.mongoHost)
    database = connessione["IntelX"]
    results = database["results"]
    schedulers = database["schedulers"]

    criterio = {"query": query}
    cursore = results.find(criterio).sort('date',pymongo.DESCENDING)


    try:
        selezione = cursore.next()
        timestamp = selezione["date"]+1 #Recupero dal secondo successivo per non avere se stesso
        print(
            "Ricerca su intelx sull data " + str(datetime.fromtimestamp(timestamp)) + " per la query " + query)
        dto = research_on_intelx(query, datetime.fromtimestamp(timestamp), None)
    except StopIteration:
        dto = research_on_intelx(query, None, None, sorter=4)
        print("Ricerca su intelx per la query " + query)
    


    if len(dto["results"]) > 0:
        results.insert_many(dto["results"])
        cursore = results.find(criterio).sort('date',pymongo.DESCENDING)
        recente = cursore.next()
        print("Trovato/i "+len(dto["results"])+ " nuovi dump. Il più recente ha id: "+recente["_id"])
        return recente["_id"]
    else: 
        print("Nessun nuovo risultato trovato")
        return None

    

def research_on_db(query):

    """
      Funzione che permette di ricercare all'interno del db i risultati associati a quella query

      :param query: query per la ricerca sul db
      :return jstr: risultato associato alla query

    """
    connessione = pymongo.MongoClient(config.mongoHost)

    # Creazione del database
    database = connessione["IntelX"]
    nuovacollection = database["results"]

    results = {}

    # Limitare i risultati da estrarre
    criterio = {"query": query}
    selezione = nuovacollection.find(criterio).sort('date',pymongo.DESCENDING)

    jstr = parse_json(selezione)  # return DTO
    
    for elemento in jstr:
        elemento["id"]=elemento["_id"]

    return jstr


def research_on_db_by_date(query, fromDate, toDate):

    """
      Funzione che permette di ricercare all'interno del db per data

      :param query, fromDate, toDate: query da ricercare, data di inizio, data di fine
      :return jstr: risultato associato alla query

    """
    connessione = pymongo.MongoClient(config.mongoHost)

    database = connessione["IntelX"]
    nuovacollection = database["results"]

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

    jstr = parse_json(selezione.sort('date',pymongo.DESCENDING))  # return DTO
    return jstr


def regular_dot(datetime_object):

    """
      Funzione che permette di formattare la data secondo il formato utile alla visualizzazione

      :param datetime_object: data da formattare
      :return data: data formattata

    """
    "regular expression per eliminare il punto dal timestamp"
    date = re.search("\d+", str(datetime_object.timestamp()))
    return int(date.group())


def DTO_creation(query, list):

    """
      Funzione che permette di creare il DTO contenete le informazioni riguardanti la ricerca su intelx

      :param query, list: query, lista dei risultati della ricerca
      :return dict_response: dizionario contenente le informazioni riguardanti la ricerca su intelx

    """

    dict_response = {}
    dict_response["id"] = uuid.uuid4()
    dict_response["query"] = query
    dict_response["timestamp"] = int(re.search("\d+", str(time.time())).group())
    dict_response["results"] = list
    return dict_response
