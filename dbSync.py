import requests
import threading
import logging
import mysql.connector
from mysql.connector import Error
import json
import argparse


LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--dbpassword", required=True, help="DB password")
args = vars(parser.parse_args())


class dbSync(threading.Thread):

    vlans = {}
    objType = "DB"

    def __init__(self, host, port, username, password, database="myDB", table="VLANS"):
        threading.Thread.__init__(self)
        self.database = database
        self.table = table
        self.connection = self.connect(host, port, username, password)
        self.createDatabase()
        self.createVLANtable()

    def connect(self, host, port, username, password):
        connection = None
        logger.info("Connecting to database...")
        try:
            connection = mysql.connector.connect(
                host=host,
                port=port,
                user=username,
                passwd=password
            )
            logger.info(f"MySQL successfully connected")
        except Error as ee:
            logger.error(f"Error trying to connect to MySQL: '{ee}'")

        return connection

    def close(self):
        self.connection.close()

    def execQuery(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.connection.commit()
        logger.debug(f"Query successful -> {query}")

    def readQuery(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        self.connection.commit()
        return results

    def createDatabase(self):
        createQuery = f"CREATE DATABASE {self.database}"
        useQuery = f"use {self.database}"
        logger.info(f"Creating database '{self.database}'...")
        try:
            self.execQuery(createQuery)
            self.execQuery(useQuery)
            logger.info(f"Using database {self.database}")
        except Error as ee:
            if ee.errno == 1007:
                logger.info(f"Database already exists!")
                self.execQuery(useQuery)
                logger.info(f"Using database {self.database}")
            else:
                logger.error(f"Error when trying to create database: '{ee}'")

            pass

    def createVLANtable(self):
        query = f'''
            CREATE TABLE {self.table} (
            ID INT UNIQUE,
            CONSTRAINT ID CHECK (ID BETWEEN 1 AND 4095),
            NAME VARCHAR(10),
            DESCRIPTION VARCHAR(100)
            );
        '''
        logger.info(f"Creating table '{self.table}' on database...")
        try:
            self.execQuery(query)
        except Error as ee:
            if ee.errno == 1050:
                logger.info(f"Table already exists!")
            else:
                logger.error(f"Error when trying to create table: '{ee}'")            

            pass

    def addOrUpdateVLAN(self, vId, name, description):
        query = f'''
            REPLACE INTO {self.table} VALUES ({vId}, '{name}', '{description}');
        '''
        try:
            self.execQuery(query)
            self.getVLANS() 
            logger.info(f"VLAN {vId} has been added/updated on DB")         
        except Error as ee:
            logger.error(f"Error when adding/updating vlan id: '{vId}'. Error: '{ee}'")
            pass

    def deleteVLAN(self, vId):
        query = f'''
            DELETE FROM {self.table} WHERE ID = {vId}
        '''
        try:
            self.execQuery(query)
            self.getVLANS()
            logger.info(f"VLAN {vId} has been deleted from DB")
        except Error as ee:
            logger.error(f"Error when trying to delete vlan id: '{vId}'. Error: '{ee}'")
            pass

    def getVLANS(self):
        query = f'''
            SELECT * FROM {self.table}
        '''
        results = {}
        logger.info("Retrieving VLANs from DB...")
        try:
            vlans = self.readQuery(query)
            for vlan in vlans:
                vId = vlan[0]
                results[vId] = {}
                results[vId]["Name"] = vlan[1]
                results[vId]["Description"] = vlan[2]

            self.vlans = results

        except Error as ee:
            logger.error(f"Error when getting VLANS from DB. VLAN list might be out of date. Error: '{ee}'")
            pass
    