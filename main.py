import json
import logging
import threading
import argparse
import time
from dbSync import dbSync
from swSync import swSync

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--dbpassword", required=True, help="DB password")
args = vars(parser.parse_args())


def checkForDeletion(aClient, aVlans, zClient, zVlans):
    '''
    Check if there's any difference between in memory vlan list and actual vlans on device/db. If any vlan has been deleted, 
    it triggers deletion on the other device. For example, if a vlan has been deleted on DB, it triggers deletion on switch.

    '''
    aClient.getVLANS()
    currentVlans = aClient.vlans

    if aVlans == currentVlans:
        return

    else:
        for aKey in aVlans:
            # if vlan not any longer, it means it's been deleted directly
            if aKey not in currentVlans: 
                # check if it exists. If so, trigger deletion
                logger.info(f"Vlan {aKey} no longer exists on {aClient.objType}!")
                if aKey in zVlans: 
                    logger.info(f"Trigger deletion on {zClient.objType} of VLAN {aKey}")
                    zClient.deleteVLAN(aKey)
        

def compareSwDB():
    '''
    Check if any vlan on switch is not on DB. If so, that vlan is added on DB.

    '''
    for swVlan in swVlans:
        if ((swVlan not in dbVlans) or (swVlans[swVlan]["Name"] != dbVlans[swVlan]["Name"])):
            logger.info(f"Need to add vlan {swVlan} on DB")
            dbClient.addOrUpdateVLAN(swVlan, swVlans[swVlan]["Name"], f"VLAN {swVlan} added automatically after discovery")


def compareDbSw():         
    '''
    Check if any vlan on DB is not on switch. If so, that vlan is added on switch

    '''
    for dbVlan in dbVlans:
        if ((dbVlan not in swVlans) or (dbVlans[dbVlan]["Name"] != swVlans[dbVlan]["Name"])):
            logger.info(f"Need to add vlan {dbVlan} on SW")
            swClient.addOrUpdateVLAN(dbVlan, dbVlans[dbVlan]["Name"])


def updateLocalVlanLists():
    '''
    Updates local copies of vlans with actual lists.

    '''
    global swVlans, dbVlans
    swVlans = swClient.vlans
    dbVlans = dbClient.vlans


if __name__ == "__main__":
    with open("./config.json", "r") as file:
        config = json.load(file)

    # initializes database connection
    dbHost = config["databaseDetails"]["host"]
    dbPort = config["databaseDetails"]["port"]
    dbUsername = config["databaseDetails"]["username"]
    dbPassword = args["dbpassword"]
    dbName = config["databaseDetails"]["dbName"]
    dbClient = dbSync(dbHost, dbPort, dbUsername, dbPassword, dbName)
    dbClient.getVLANS()
    # saves locally a copy of current vlans on DB
    dbVlans = dbClient.vlans

    # initializes switch connection
    swHostname= config["switchDetails"]["switch"]
    swUsername = config["switchDetails"]["username"]
    swPKey = config["switchDetails"]["privateKeyPath"]
    swClient = swSync(swHostname, swUsername, swPKey)
    swClient.getVLANS()
    # saves locally a copy of current vlans on DB
    swVlans = swClient.vlans
    
    try:
        while True:
            print()
            time.sleep(5)

            # check if any vlan on switch has been deleted
            checkForDeletion(swClient, swVlans, dbClient, dbVlans)
            updateLocalVlanLists()
            # check if any vlan on DB hast been deleted
            checkForDeletion(dbClient, dbVlans, swClient, swVlans)
            updateLocalVlanLists()           

            # check if any vlan on switch is not on DB
            compareSwDB()
            updateLocalVlanLists()
            # check if any vlan on DB is not on switch
            compareDbSw()
            updateLocalVlanLists()

    except KeyboardInterrupt:
        dbClient.close()
        logger.info("User has terminated the process")
