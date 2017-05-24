'''
Created on may 2017

@author: davidemaraschio

'''

from do_core.rest import ONOS
from do_core.exception import BridgeNotFound, OnosInternalError
import json, logging

'''
This is a business class. This class interacts with onos Rest api to handle the requests from controller

'''

class ONOSBusiness(object):

    def __init__(self, onos_endpoint, onos_username, onos_password):
        self.onosEndpoint = onos_endpoint
        self.onosUsername = onos_username
        self.onosPassword = onos_password

	def getOvsdbIP(self):
		response = ONOS().getOvsdbIP(self.onosEndpoint, self.onosUsername, self.onosPassword)
		devices = response.text

	        json_object = json.loads(devices)['devices']

		for node in json_object:
			if node['id'].split(':')[0] == 'ovsdb':
				return node['id'].split(":")[1]

		raise OVSDBNodeNotFound("No OVSDB connection found!")

	def getBridgePorts(self, bridge_name):
		bridgeID = ONOS().getBridgeID(self.onosEndpoint, self.onosUsername, self.onosPassword, bridge_name)
		response = ONOS().getPorts(self.onosEndpoint, self.onosUsername, self.onosPassword, bridgeID)

		if response.status_code is 404:
			raise BridgeNotFound(port + " not found")

		device = response.text

	        json_object = json.loads(device)['ports']

		return len(json_object)


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
		response = ONOS().createPatchPort(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP,, bridge_name, port_name, patch_peer)
		if response.status_code is 404:
			raise BridgeNotFound(port + " not found")
		elif response.status_code is 500:
			raise OnosInternalError("500 Internal Server Error " + response.text)

	def createGreTunnel(self, ovsdbIP, bridge_name, port_name, local_ip, remote_ip, tunnel_key):
		response = ONOS().createGreTunnel(self.onosEndpoint, self.onosUsername, self.onosPassword, ovsdbIP, bridge_name, port_name, local_ip, remote_ip, tunnel_key)
		if response.status_code is 404:
			raise BridgeNotFound(port + " not found")
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


