import paramiko
import logging
import json
import threading
import re
import time


LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class swSync(threading.Thread):

    vlans = {}
    objType = "switch"

    def __init__(self, swHostname, swUsername, swPrivateKeyPath):
        threading.Thread.__init__(self)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.hostname = swHostname
        self.username = swUsername
        self.pKey = paramiko.RSAKey.from_private_key_file(swPrivateKeyPath)

    def execCommand(self, command):
        err = False
        output = None
        try:
            self.client.connect(hostname=self.hostname, username=self.username, pkey=self.pKey)
            logger.debug(f"Connected to {self.hostname}")
            logger.debug(f"Executing command: {command}")
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.readlines()
            self.client.close()
        except Exception as ee:
            logger.error(f"Error when trying to execute remote command: {ee}")
            err = True
            pass

        return output, err

    def getVLANS(self):
        results = {}
        output, err = self.execCommand("show vlan")
        # output, err = self.execCommand("cat vlan")
        logger.info("Retrieving VLANs from switch...")
        if not err:
            for i in range(2, len(output)):
                data = re.split(' +', output[i])
                vId = int(data[0])
                results[vId] = {}
                results[vId]["Name"] = data[1]

            self.vlans = results
        else:
            logger.error(f"An error occurred when trying to retrieve vlans from switch. VLAN list might be out of date. Error '{err}'")


    def addOrUpdateVLAN(self, vId, name):
        try:
            self.client.connect(hostname=self.hostname, username=self.username, pkey=self.pKey)
            logger.debug(f"Connected to {self.hostname}")

            conn = self.client.invoke_shell()

            conn.send("conf t\n")
            time.sleep(.5)
            output = conn.recv(65535)

            conn.send(f"vlan {vId}\n")
            time.sleep(.5)
            output = conn.recv(65535)

            conn.send(f"name {name}\n")
            time.sleep(.5)
            output = conn.recv(65535)

            conn.send("exit\n")
            time.sleep(.5)
            output = conn.recv(65535)

            conn.send("write memory\n")
            time.sleep(.5)
            output = conn.recv(65535)

            conn.send("end\n")
            time.sleep(.5)
            output = conn.recv(65535)

            logger.info(f"VLAN {vId} has been added/updated on switch")
            self.getVLANS()

        except Exception as ee:
            logger.error(f"An error occurred when trying to add/update vlan {vId} on switch. Error: '{ee}'")
            pass

        # output, err = self.execCommand(f"echo '{vId}   {name}                          active    Fa5/9' >> /home/ubuntu/vlan")
        # if not err:
        #     logger.info(f"VLAN {vId} has been added/updated on switch")
        #     self.getVLANS()
        # else:
        #     logger.error(f"An error occurred when trying to add/update vlan {vId}")


    def deleteVLAN(self, vId):
        try:
            self.client.connect(hostname=self.hostname, username=self.username, pkey=self.pKey)
            logger.debug(f"Connected to {self.hostname}")

            conn = self.client.invoke_shell()

            conn.send("conf t\n")
            time.sleep(.5)
            output = conn.recv(65535)

            conn.send(f"no vlan {vId}\n")
            time.sleep(.5)
            output = conn.recv(65535)

            conn.send("exit\n")
            time.sleep(.5)
            output = conn.recv(65535)

            conn.send("write memory\n")
            time.sleep(.5)
            output = conn.recv(65535)

            conn.send("end\n")
            time.sleep(.5)
            output = conn.recv(65535)

            logger.info(f"VLAN {vId} has been deleted from switch")
            self.getVLANS()

        except Exception as ee:
            logger.error(f"An error occurred when trying to delete vlan {vId} on switch. Error: '{ee}'")
            pass

        # output, err = self.execCommand(f"sed -i '/^{vId} /'d vlan /home/ubuntu/vlan")
        # if not err:
        #     logger.info(f"VLAN {vId} has been deleted from switch")
        #     self.getVLANS()
        # else:
        #     logger.error(f"An error occurred when trying to add/update vlan {vId}")

