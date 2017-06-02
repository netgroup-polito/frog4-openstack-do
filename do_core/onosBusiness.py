'''
Created on may 2017

@author: ReliableLion

'''

from do_core.rest import ONOS
from do_core.exception import BridgeNotFound, OnosInternalError, OVSDBNodeNotFound, PortNotFound
import json, logging, requests

'''
This is a business class. This class interacts with onos Rest api to handle the requests from controller

'''

class ONOSBusiness(object):

    def __init__(self, onos_endpoint, onos_username, onos_password):
        self.onosEndpoint = onos_endpoint
        self.onosUsername = onos_username
        self.onosPassword = onos_password
        self.appID = 'org.onosproject.ovsdbrest'

    '''
    The nodeIP should be the same of ovsdb ip. That's because nodeIP is an ip address representing a node where ovsdb is running and it's used by onos as management address for that node
    '''
    def getOvsdbIP(self, nodeIP):
        response = ONOS().getOvsdbIP(self.onosEndpoint, self.onosUsername, self.onosPassword)
        devices = response.text

        json_object = json.loads(devices)['devices']

        for node in json_object:
            if node['id'].split(':')[0] == 'ovsdb' and node['id'].split(":")[1] == nodeIP:
                return node['id'].split(":")[1]

        raise OVSDBNodeNotFound("No OVSDB connection found for " + nodeIP)

    def getBridgeID(self, ovsdbIP, bridge_name):
        bridgeID = ONOS().getBridgeID(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name)

        if bridgeID.status_code is 200:
            return bridgeID.text

        else:
            raise BridgeNotFound(bridge_name + " not found")

    def getBridgePorts(self, ovsdbIP, bridge_name):
        bridgeID = ONOS().getBridgeID(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name)
        if bridgeID.status_code is 200:
            response = ONOS().getPorts(self.onosEndpoint, self.onosUsername, self.onosPassword, bridgeID.text)

        else:
            raise BridgeNotFound(bridge_name + " not found")

        if response.status_code is 404:
            raise BridgeNotFound(bridge_name + " not found")

        device = response.text

        json_objects = json.loads(device)['ports']

        return len(json_objects)

    def getOfPort(self, ovsdbIP, bridge_name, isAVNF, portID):

        print("I'm in getOfPort" + ovsdbIP)
        print(bridge_name)
        print(portID)
        bridgeID = ONOS().getBridgeID(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name)

        if bridgeID.status_code is 200:
            response = ONOS().getPorts(self.onosEndpoint, self.onosUsername, self.onosPassword, bridgeID.text)

        else:
            raise BridgeNotFound(bridge_name + " not found")

        if response.status_code is 404:
            raise BridgeNotFound(bridge_name + " not found by ID")

        device = response.text

        json_objects = json.loads(device)['ports']

        vnfPort = "tap"+str(portID)
        print(vnfPort)

        for port in json_objects:
            #print("CONFRONTO: " + port['annotations']['portName'] + " CON " + vnfPort)
            if port['annotations']['portName'] == vnfPort:
                return port['port']

        for port in json_objects:
            #print("NON ERA UNA VNF!!!!!!!!!!!!!!!!!!!!!!! CONFRONTO: " + port['annotations']['portName'] + " CON " + str(port))
            if port['annotations']['portName'] == str(portID):
                return port['port']

        print("NON HO TROVATO: " + str(portID))

        raise PortNotFound(str(portID) + " not found")

    def getHostBridgeID(self, vnfPort):
        response = ONOS().getHostBridgeID(self.onosEndpoint, self.onosUsername, self.onosPassword, vnfPort)

        hosts = response.text

        jsonHost = json.loads(hosts)['hosts']
        print(vnfPort)
        for host in jsonHost:
            print(host['annotations']['portId'][0:11])
            if host['annotations']['portId'][0:11] == vnfPort:
                return host['location']['elementId']

        raise PortNotFound(vnfPort + " not found")

    def getBridgeOvdbNodeIP(self, brID):
        bridgeInfo = ONOS().getBridgeOvdbNodeIP(self.onosEndpoint, self.onosUsername, self.onosPassword, brID)

        bridge = json.loads(bridgeInfo.text)['annotations']

        if bridge is not None:

            return bridge['managementAddress']

        raise BridgeNotFound(bridge_name + " not found")

    def createFlow(self, json_req):
        response = ONOS().createFlow(self.onosEndpoint, self.onosUsername, self.onosPassword, self.appID, json_req)
        print(response.status_code)

        if response.status_code is 200:

            flowResponse = response.text
            json_object = json.loads(flowResponse)['flows']

            for flowID in json_object:
                return flowID['flowId']

        else:
            response.raise_for_status()
            return None

    def deleteFlow(self, of_switch_id, flowID):

        response = ONOS().deleteFlow(self.onosEndpoint, self.onosUsername, self.onosPassword, of_switch_id, flowID)

        if response.status_code is 500:
            raise OnosInternalError("500 Internal Server Error " + response.text)

    def createBridge(self, ovsdbIP, bridge_name):
        response = ONOS().createBridge(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name)
        if response.status_code is 500:
            raise OnosInternalError("500 Internal Server Error " + response.text)

    def createPort(self, ovsdbIP, bridge_name, port_name):
        response = ONOS().createPort(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name, port_name)
        if response.status_code is 404:
            raise BridgeNotFound(port + " not found")
        elif response.status_code is 500:
            raise OnosInternalError("500 Internal Server Error " + response.text)

    def createPatchPort(self, ovsdbIP, bridge_name, port_name, patch_peer):
        response = ONOS().createPatchPort(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name, port_name, patch_peer)
        if response.status_code is 404:
            raise BridgeNotFound(port + " not found")
        elif response.status_code is 500:
            raise OnosInternalError("500 Internal Server Error " + response.text)

    def createGreTunnel(self, ovsdbIP, bridge_name, port_name, local_ip, remote_ip, tunnel_key):
        response = ONOS().createGreTunnel(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name,
                                          port_name, local_ip, remote_ip, tunnel_key)
        if response.status_code is 404:
            raise BridgeNotFound(bridge_name + " not found")
        elif response.status_code is 500:
            raise OnosInternalError("500 Internal Server Error " + response.text)

    def deleteBridge(self, ovsdbIP, bridge_name):
        response = ONOS().deleteBridge(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name)
        if response.status_code is not 200:
            raise OnosInternalError(response.status_code + " " + response.text)

    def deletePort(self, ovsdbIP, bridge_name, port_name):
        response = ONOS().deletePort(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name, port_name)
        if response.status_code is not 200:
            raise OnosInternalError(response.status_code + " " + response.text)

    def deleteGreTunnel(self, ovsdbIP, bridge_name, port_name):
        response = ONOS().deleteGreTunnel(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name, port_name)
        if response.status_code is not 200:
            raise OnosInternalError(response.status_code + " " + response.text)


