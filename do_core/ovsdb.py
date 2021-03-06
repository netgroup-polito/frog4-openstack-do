'''
Created on 03 giu 2016

@author: stefanopetrangeli
'''

from do_core.rest import ODL
from do_core.exception import OVSDBNodeNotFound, BridgeNotFound, PortNotFound
import json, logging


class OVSDB(object):
    def __init__(self, odl_endpoint, odl_username, odl_password, ovs_id = None):
        self.odlendpoint = odl_endpoint
        self.odlusername = odl_username
        self.odlpassword = odl_password
        self.ovs_id = ovs_id

    def getBridgeDPID(self, ovs_id, bridge_name):
        bridges = ODL().getOVSDBTopology(self.odlendpoint, self.odlusername, self.odlpassword)
        json_object = json.loads(bridges)['topology'][0]['node']
        datapath_id = None
        for node in json_object:
            if 'ovsdb:bridge-name' in node and node['ovsdb:bridge-name'] == bridge_name and ovs_id in node['node-id']:
                datapath_id = node['ovsdb:datapath-id']
                break
        if datapath_id is None:
            raise BridgeNotFound(bridge_name + " not found")
        return datapath_id
    
    def getBridgeUUID(self, ovs_id, bridge_name):
        bridges = ODL().getOVSDBTopology(self.odlendpoint, self.odlusername, self.odlpassword)
        json_object = json.loads(bridges)['topology'][0]['node']
        for node in json_object:
            if 'ovsdb:bridge-name' in node and node['ovsdb:bridge-name'] == bridge_name and ovs_id in node['node-id']:
                return node['ovsdb:bridge-uuid'] #Needed??
        return None
    
    def getOVSId(self, node_ip):
        topology = ODL().getOVSDBTopology(self.odlendpoint, self.odlusername, self.odlpassword)
        json_object = json.loads(topology)['topology'][0]['node']
        node_id = None
        for node in json_object:
            if 'ovsdb:connection-info'in node and node['ovsdb:connection-info']['remote-ip'] == node_ip:
                node_id = node['node-id']
                break
        if node_id is None:
            raise OVSDBNodeNotFound("NO OVSDB Connection found for "+node_ip)
        return node_id


    def getOfPort(self, ovs_id, bridge_name, port_id):
        bridge_data = ODL().getBridge(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name)
        #logging.debug(bridge_data)
        termination_points = json.loads(bridge_data)['node'][0]['termination-point']
        for termination_point in termination_points:
            if port_id in termination_point['tp-id']:
                return termination_point['ovsdb:ofport']
        logging.debug(bridge_data)
        raise PortNotFound(port_id + " not found")
    
    def getBridgePorts(self, ovs_id, bridge_name):
        bridge_data = ODL().getBridge(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name)
        #logging.debug(bridge_data)
        termination_points = json.loads(bridge_data)['node'][0]['termination-point']
        return termination_points
        
    def createPort(self, ovs_id, port_name, bridge_name, vlan=None):
        if ODL().getPort(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name, port_name) is None:
            ODL().createPort(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name, port_name, vlan)
    
    def createPatchPort(self, ovs_id, port_name, bridge_name, patch_peer, vlan=None):
        if ODL().getPort(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name, port_name) is None:
            ODL().createPatchPort(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name, port_name, patch_peer, vlan)
    
    def createGrePort(self, ovs_id, port_name, bridge_name, gre_local_ip, gre_remote_ip, gre_key):
        if ODL().getPort(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name, port_name) is None:
            ODL().createGrePort(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name, port_name, gre_local_ip, gre_remote_ip, gre_key)
                
    def createBridge(self, ovs_id, bridge_name):
        if ODL().getBridge(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name) is None:
            ODL().createBridge(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name)
        
    def deletePort(self, ovs_id, port_name, bridge_name):
        ODL().deletePort(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name, port_name)
            
    def deleteBridge(self, ovs_id, bridge_name):
        ODL().deleteBridge(self.odlendpoint, self.odlusername, self.odlpassword, ovs_id, bridge_name)
