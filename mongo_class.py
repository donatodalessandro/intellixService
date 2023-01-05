import os
import time
from bson import json_util
from intelxapi import intelx
from flask import Flask, jsonify
import json
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from paho.mqtt.client import Client

# Importazione del modulo di PyMongo
import pymongo


def creazioneDB(lista):

    print("database")
    connessione = pymongo.MongoClient()

    # Creazione del database
    database = connessione["IntelX"]
    nuovacollection = database["results"]

    # Estrazione dei documenti di una collection

    '''
    for selezione in nuovacollection.find():
        for elem in lista:
            if elem['query'] == selezione['query']:
                lista.remove(elem)
    '''

    nuovacollection.insert_one(lista)


def drop_collection(query):

    connessione = pymongo.MongoClient("mongodb://localhost:27017/")

    # Creazione del database
    database = connessione["IntelX"]
    results_collection = database["results"]
    schedulers_collection = database["schedulers"]
    # Rimuovere dati da una collection
    criterio = {"query": query}
    results_collection.delete_many(criterio)
    schedulers_collection.delete_many(criterio)

    return jsonify('Drop successfully!')