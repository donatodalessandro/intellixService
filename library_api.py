from cheroot import wsgi
from datetime import datetime
from flask import Flask, request
import re
import backend
from models import SearchCommand, ScheduleCommand, TokenCommand
import time
import uuid
import config


class Config:
    SCHEDULER_API_ENABLED=True
    MQTT_BROKER_URL = config.mqttBroker
    MQTT_BROKER_PORT = config.mqttBrokerPort
    MQTT_REFRESH_TIME = 1.0


app = Flask(__name__)
app.config.from_object(Config())


@app.route(config.basepath+'/token', methods=['PUT','GET'])
def set_token():

    """
        Funzione che permette di settare il token mediante il metodo PUT o acquisirlo mediante il metodo GET

        :return: in base al tipo di metodo Http il token verrà settato o ritornato come json

    """

    if request.method == 'PUT':
        print("Invocato servizio di modifica token")
        tokenCommand = TokenCommand(request.json)
        backend.set_token(tokenCommand.token)
        print("Token modificato")
        return {}
    else:
        print("Invocato servizio di recupero token")
        return {"token": backend.get_token()}


@app.post(config.basepath+'/searches')
def research_by_domain():
    print("Invocato servizio di ricerca diretta da IntelX")

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
        print("I dati richiesti sono già sul database, si procede all'invio")
        return dict_response
    else:
        print("I dati richiesti non sono presenti sul database, avvio ricerca su intelX")
        return backend.research_on_intelx(query, fromDate, toDate)

@app.route(config.basepath+'/schedulers', methods=['POST'])
def research_schedulers():
    """
        Endpoint Rest per l'attivazione dell'alert per verificare la presenza di un nuovo dump

        :return: Lista contenete i dump in formato json

    """
    

    scheduleCommand = ScheduleCommand(request.json)
    query = scheduleCommand.query
    print("Invocato servizio di aggiunta alert per la query "+query)
    return backend.research_scheduler(query)

#DOVREBBE ESSERE UNA DELETE, MA A FLASK LE DELETE NON TANTO PIACCIONO, BLOCCANDO TUTTO
@app.put(config.basepath+'/schedulers/<query>')
def delete_schedulers(query):
    print("Invocato servizio di rimozione alert")
    """
        Funzione che permette di eliminare dalla collezione nel database lo scheduler associato alla query

        :param query: scheduler da eliminare
        :return:

    """

    return backend.drop_collection(query)



@app.get(config.basepath+'/searches/<query>')
def last_results_from_query(query):
    print("Invocato servizio per la restituzione dei dati dal db per la query "+query)
    """
        Funzione che ritorna i risultati della ricerca per query sul database

        :return: DTO contenente i risultati della ricerca su db

    """
    return backend.DTO_creation(query, backend.research_on_db(query))


if __name__ == '__main__':
    addr = '0.0.0.0', 5002
    server = wsgi.Server(addr, app)
    
    try:
        print("Server starting")
        server.start()

    
    except KeyboardInterrupt:
        server.stop()
        print("-----------------Debug message: server stopped")
    
    except Exception as e:
        print(e)
