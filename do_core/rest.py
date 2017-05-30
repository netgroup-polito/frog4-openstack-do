'''
Created on 15 apr 2016

@author: vida
@author: stefanopetrangeli
@author: ReliableLion
'''

import requests, urllib
import json, logging

'''
######################################################################################################
##############################               ONOS  REST calls            ##############################
######################################################################################################
'''

'''
   This class interacts with an ONOS app, ovsdbrest, which exhibits REST api for the following actions:
    - Create/delete a bridge
    - Add/delete a port
    - Add/delete a patch port (see man 5 ovs-vswitchd.conf.db for more info)
    - Add/delete a GRE tunnel (see http://api.onosproject.org/1.7.1/org/onosproject/net/behaviour/DefaultTunnelDescription.Builder.html for more info about GRE tunnel in ONOS)
'''
class ONOS(object):

    def __init__(self):
        self.onos_api         = '/onos/v1'
        self.onos_bridge_path = '/onos/ovsdb/%s/bridge/%s'
        self.onos_port_path   = '/port/%s'
        self.onos_patch_path  = '/patch_peer/'
        self.onos_gre_path    = '/gre'
        self.onos_devices     = '/devices'
        self.onos_api_port    = '/%s/ports'
        self.onos_api_flow    = '/flows'

    def getOvsdbIP(self, onos_endpoint, onos_user, onos_pass):
        '''
        Get all devices.
        '''
        headers = {'Accept': 'application/json'}
        
        url = onos_endpoint + self.onos_api + self.onos_devices
        
        response = requests.get(url, headers=headers, auth=(onos_user, onos_pass))

        return response

    #This method returns 200 OK if it sucessful creates a bridge, 409 Conflict if the bridge already exists (There's no getBridge method), 500 otherwise
    def createBridge(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, br_name):
        '''
        Create a bridge
        Args:
            br_name: name of the bridge
            ovsdb_ip: The endpoint to the ovsdb node where the bridge are
        '''
        headers = {'Accept': 'text/plain', 'Content-type': 'text/plain'}
        
        bridge_path = self.onos_bridge_path % (ovsdb_ip, br_name)
        url = onos_endpoint + bridge_path
        
        response = requests.post(url, headers=headers, auth=(onos_user, onos_pass))

        return response

    def getPorts(self, onos_endpoint, onos_user, onos_pass, br_ID):
        '''
        Retrieve a port number given the ID of a bridge
        Args:
            br_name: name of the bridge
        '''
        headers = {'Accept': 'application/json'}

        url = onos_endpoint + self.onos_api + self.onos_devices + self.onos_api_port % (br_ID)
        
        response = requests.get(url, headers=headers, auth=(onos_user, onos_pass))

        return response

    #This method returns 200 OK if it sucessful retrieve a bridge ID, 404 if the bridge doesn't exists
    def getBridgeID(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, br_name):
        '''
        Retrieve a bridge ID from name
        Args:
            br_name: name of the bridge
        '''
        headers = {'Accept': 'text/plain'}
        
        bridge_path = self.onos_bridge_path % (ovsdb_ip, br_name)

        url = onos_endpoint + bridge_path
        
        response = requests.get(url, headers=headers, auth=(onos_user, onos_pass))

        return response

    #This method returns 200 OK if it sucessful retrieve a bridge ID, 404 if the bridge doesn't exists
    def getBridgePorts(self, onos_endpoint, onos_user, onos_pass, br_id):
        '''
        Get the ports of a bridge
        Args:
            br_id: ID of the bridge
            ovsdb_ip: The endpoint to the ovsdb node where the bridge is
        '''
        headers = {'Accept': 'text/plain'}
        
        device_path = self.onos_api + self.onos_devices + '/' + br_id + '/ports'

        url = onos_endpoint + urllib.parse.quote(device_path, safe='')
        
        response = requests.post(url, headers=headers, auth=(onos_user, onos_pass))

        return response

    #This method returns 200 OK if it sucessful create and attach a port, 404 if the related bridge doesn't exist, 409 if the port already exists (There's no getPort method), 500 otherwise
    def createPort(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, br_name, port_name):
        '''
        Attach a port to a specified bridge
        Args:
            br_name: Name of the bridge
            ovsdb_ip: The endpoint to the ovsdb node where the bridge is
            port_name: Name of the port to attach
        '''
        headers = {'Accept': 'text/plain', 'Content-type': 'application/json'}
        
        bridge_path = self.onos_bridge_path % (ovsdb_ip, br_name)
        port_path = self.onos_port_path % (port_name)
        url = onos_endpoint + urllib.parse.quote(bridge_path, safe='') + urllib.parse.quote(port_path, safe='')

        response = requests.post(url, headers=headers, auth=(onos_user, onos_pass))

        return response

    #This method returns 200 OK if it sucessful create and attach a port, 404 if the related bridge doesn't exist, 409 if the port already exists (There's no getPort method), 500 otherwise
    def createPatchPort(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, br_name, port_name, patch_peer):
        '''
        Create and attach a patch port to a specified bridge
        Args:
            br_name: Name of the bridge
            ovsdb_ip: The endpoint to the ovsdb node where the bridge is
            port_name: Name of the port to attach
            patch_peer: This is the name of the peer port
        '''
        headers = {'Accept': 'text/plain', 'Content-type': 'application/json'}
        
        bridge_path = self.onos_bridge_path % (ovsdb_ip, br_name)
        patch_path = self.onos_port_path % (port_name) + self.onos_patch_path + patch_peer
        url = onos_endpoint + urllib.parse.quote(bridge_path, safe='') + urllib.parse.quote(patch_path, safe='')

        response = requests.post(url, headers=headers, auth=(onos_user, onos_pass))

        return response.status_code

    #This method returns 200 OK if it sucessful create a GRE tunnel, 404 if the related bridge doesn't exist, 500 otherwise
    def createGreTunnel(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, br_name, port_name, local_ip, remote_ip, tunnel_key):
        '''
        Create a Gre tunnel with a specific tunnel key
        Args:
            br_name: Name of the bridge
            ovsdb_ip: The endpoint to the ovsdb node where the bridge is
            port_name: Name of the port to attach
            local_ip: The local IP address (local GRE endpoint)
            remote_ip: The remote IP address (remote GRE endpoint)
            tunnel_key: This is the Tunnel key, usually (for GRE tunnel) a 32-bit number value
        '''
        headers = {'Accept': 'text/plain', 'Content-type': 'application/json'}

        bridge_path = self.onos_bridge_path % (ovsdb_ip, br_name)
        port_path = self.onos_port_path % (port_name)
        gre_path = self.onos_gre_path + '/' + local_ip + '/' + remote_ip + '/' + tunnel_key
        url = onos_endpoint + urllib.parse.quote(bridge_path, safe='') + urllib.parse.quote(port_path, safe='') + urllib.parse.quote(gre_path, safe='')

        response = requests.post(url, headers=headers, auth=(onos_user, onos_pass))

        return response.status_code

    #This method returns 200 OK if it sucessful delete a bridge, 500 otherwise
    def deleteBridge(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, br_name):
        '''
        Create a bridge
        Args:
            br_name: name of the bridge
            ovsdb_ip: The endpoint to the ovsdb node where the bridge is
        '''
        headers = {'Accept': 'text/plain', 'Content-type': 'text/plain'}
        
        bridge_path = self.onos_bridge_path % (ovsdb_ip, br_name)
        url = onos_endpoint + urllib.parse.quote(bridge_path, safe='')
        
        response = requests.delete(url, headers=headers, auth=(onos_user, onos_pass))

        return response.status_code

    #This method returns 200 OK if it sucessful delete a port/patch port, 404 if the related bridge doesn't exist, 500 otherwise
    def deletePort(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, br_name, port_name):
        '''
        Attach a port to a specified bridge
        Args:
            br_name: Name of the bridge
            ovsdb_ip: The endpoint to the ovsdb node where the bridge are
            port_name: Name of the port to attach
        '''
        headers = {'Accept': 'text/plain', 'Content-type': 'application/json'}
        
        bridge_path = self.onos_bridge_path % (ovsdb_ip, br_name)
        port_path = self.onos_port_path % (port_name)
        url = onos_endpoint + urllib.parse.quote(bridge_path, safe='') + urllib.parse.quote(port_path, safe='')

        response = requests.delete(url, headers=headers, auth=(onos_user, onos_pass))

        return response.status_code

    #This method returns 200 OK if it sucessful delete a GRE tunnel, 500 otherwise
    def deleteGreTunnel(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, br_name, port_name):
        '''
        Create a Gre tunnel with a specific tunnel key
        Args:
            br_name: Name of the bridge
            ovsdb_ip: The endpoint to the ovsdb node where the bridge is
            port_name: Name of the port to attach
            local_ip: The local IP address (local GRE endpoint)
            remote_ip: The remote IP address (remote GRE endpoint)
            tunnel_key: This is the Tunnel key, usually (for GRE tunnel) a 32-bit number value
        '''
        headers = {'Accept': 'text/plain', 'Content-type': 'application/json'}

        bridge_path = self.onos_bridge_path % (ovsdb_ip, br_name)
        port_path = self.onos_port_path % (port_name)

        url = onos_endpoint + urllib.parse.quote(bridge_path, safe='') + urllib.parse.quote(port_path, safe='') + self.onos_gre_path

        response = requests.delete(url, headers=headers, auth=(onos_user, onos_pass))

        return response.status_code

    def createFlow(self, onos_endpoint, onos_user, onos_pass, app_id, json_req):
        '''
        Create a flow
        Args:
            app_id: It's used to know to which app each node is related. It's useful when you have a lot of flows and there are problem in the network,
                    in this case you can delete all the flows, belonging to an app, which are causing the problem
            json_req: The json that describes the flow
        '''
        headers = {'Accept': 'application/json', 'Content-type': 'application/json'}
        parameter = {'appId': app_id}

        url = onos_endpoint + self.onos_api + self.onos_api_flow

        response = requests.post(url, json_req, params=parameter, headers=headers, auth=(onos_user, onos_pass))
        print(response.url)

        return response

    def deleteFlow(self, onos_endpoint, onos_user, onos_pass, of_switch_id, flowID):
        '''
        Delete a flow
        Args:
            of_switch_id: Openflow ID of the device which the flowRule refers to
            flowID: ID of the flow to delete
        '''

        url = onos_endpoint + self.onos_api + self.onos_api_flow +'/' + of_switch_id + '/' + flowID

        response = requests.delete(url, auth=(onos_user, onos_pass))
        print(response.url)

        return response

'''
######################################################################################################
############################    OpenDaylight  REST calls        ################################
######################################################################################################
'''

class ODL(object):
    
    def __init__(self):
        self.odl_nodes_path = "/restconf/operational/opendaylight-inventory:nodes"
        self.odl_topology_path = "/restconf/operational/network-topology:network-topology/"
        self.odl_config_topology_path = "/restconf/config/network-topology:network-topology/"
        self.odl_flows_path = "/restconf/config/opendaylight-inventory:nodes"
        self.odl_node="/node/"
        self.odl_flow="/table/%s/flow/"
        self.odl_ovsdb_topology="topology/ovsdb:1"
        self.odl_bridge_path = "%s/bridge/%s"
        self.odl_port_path = "/termination-point/"

    
    def getNodes(self, odl_endpoint, odl_user, odl_pass):
        '''
        Deprecated with Cisco switches because response is not a valid JSON
        '''
        headers = {'Accept': 'application/json'}
        url = odl_endpoint+self.odl_nodes_path
        resp = requests.get(url, headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text
    
    def getOVSDBTopology(self, odl_endpoint, odl_user, odl_pass):
        '''
        '''
        headers = {'Accept': 'application/json'}
        url = odl_endpoint + self.odl_topology_path + self.odl_ovsdb_topology
        resp = requests.get(url, headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text
    """
    def getTopology(self, odl_endpoint, odl_user, odl_pass):
        '''
        Get the entire topology comprensive of hosts, switches and links (JSON)
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        '''
        headers = {'Accept': 'application/json'}
        url = odl_endpoint+self.odl_topology_path
        resp = requests.get(url, headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text
    """
    
    def getBridge(self, odl_endpoint, odl_user, odl_pass, ovs_id, bridge_name):
        headers = {'Accept': 'application/json'}
        bridge_path = self.odl_bridge_path % (ovs_id, bridge_name)
        url = odl_endpoint +self.odl_topology_path + self.odl_ovsdb_topology+ self.odl_node + urllib.parse.quote(bridge_path, safe='')
        resp = requests.get(url, headers=headers, auth=(odl_user, odl_pass))
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.text
    
    def getPort(self, odl_endpoint, odl_user, odl_pass, ovs_id, bridge_name, port_name):
        headers = {'Accept': 'application/json'}
        port_path = self.odl_bridge_path % (ovs_id, bridge_name) + self.odl_port_path + port_name
        url = odl_endpoint +self.odl_topology_path + self.odl_ovsdb_topology+ self.odl_node + urllib.parse.quote(port_path, safe='')
        resp = requests.get(url, headers=headers, auth=(odl_user, odl_pass))
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.text
    
    def createBridge(self, odl_endpoint, odl_user, odl_pass, ovs_id, name):
        '''
        Args:
            name:
                name of the bridge
            ovs_id:
                The endpoint to the node where the bridges are
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        bridge_path = self.odl_bridge_path % (ovs_id, name)
        url = odl_endpoint +self.odl_config_topology_path + self.odl_ovsdb_topology+ self.odl_node + urllib.parse.quote(bridge_path, safe='')
        body = {"network-topology:node": [{
            "node-id": bridge_path,
            "ovsdb:bridge-name": name,
            "ovsdb:protocol-entry": [
            {"protocol": "ovsdb:ovsdb-bridge-protocol-openflow-13"}
            ],
            "ovsdb:managed-by": "/network-topology:network-topology/network-topology:topology[network-topology:topology-id='ovsdb:1']/network-topology:node[network-topology:node-id='"+ovs_id+"']"}]}
        resp = requests.put(url, data=json.dumps(body), headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text
    
    def createPort(self, odl_endpoint, odl_user, odl_pass, ovs_id, bridge_name, port_name, vlan=None):
        '''
        Args:
            name:
                name of the bridge
            ovs_id:
                The endpoint to the node where the bridges are
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        bridge_path = self.odl_bridge_path % (ovs_id, bridge_name)
        url = odl_endpoint +self.odl_config_topology_path + self.odl_ovsdb_topology+ self.odl_node + urllib.parse.quote(bridge_path, safe='') + self.odl_port_path + port_name
        if vlan is None:
           body = {"network-topology:termination-point": [{"ovsdb:name": port_name,"tp-id": port_name}]}
        else:
           body = {"network-topology:termination-point": [{"ovsdb:name": port_name,"tp-id": port_name, "ovsdb:vlan-tag": vlan}]}

        resp = requests.put(url, data=json.dumps(body), headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text
    
    def createPatchPort(self, odl_endpoint, odl_user, odl_pass, ovs_id, bridge_name, port_name, patch_peer,vlan=None):
        '''
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        bridge_path = self.odl_bridge_path % (ovs_id, bridge_name)
        url = odl_endpoint +self.odl_config_topology_path + self.odl_ovsdb_topology+ self.odl_node + urllib.parse.quote(bridge_path, safe='') + self.odl_port_path + port_name
        if vlan is not None:
           body= {"network-topology:termination-point": [{
             "ovsdb:options": [
             {
              "ovsdb:option": "peer",
              "ovsdb:value" : patch_peer
             }
             ],
             "ovsdb:name": port_name,
             "ovsdb:interface-type": "ovsdb:interface-type-patch",
             "tp-id": port_name,
             "ovsdb:vlan-tag": vlan}]}
        else:
          body= {"network-topology:termination-point": [{
             "ovsdb:options": [
             {
              "ovsdb:option": "peer",
              "ovsdb:value" : patch_peer
             }
             ],
             "ovsdb:name": port_name,
             "ovsdb:interface-type": "ovsdb:interface-type-patch",
             "tp-id": port_name}]}

        resp = requests.put(url, data=json.dumps(body), headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text
    
    def createGrePort(self, odl_endpoint, odl_user, odl_pass, ovs_id, bridge_name, port_name, gre_local_ip, gre_remote_ip, gre_key):
        '''
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        bridge_path = self.odl_bridge_path % (ovs_id, bridge_name)
        url = odl_endpoint +self.odl_config_topology_path + self.odl_ovsdb_topology+ self.odl_node + urllib.parse.quote(bridge_path, safe='') + self.odl_port_path + port_name
        body= {"network-topology:termination-point": [{
          "ovsdb:options": [
            {
              "ovsdb:option": "local_ip",
              "ovsdb:value" : gre_local_ip
            },
            {
              "ovsdb:option": "remote_ip",
              "ovsdb:value" : gre_remote_ip
            },        
            {
              "ovsdb:option": "key",
              "ovsdb:value" : gre_key
            },                                               
                            
          ],
          "ovsdb:name": port_name,
          "ovsdb:interface-type": "ovsdb:interface-type-gre",
          "tp-id": port_name}]}
        resp = requests.put(url, data=json.dumps(body), headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text    
    
    def deletePort(self, odl_endpoint, odl_user, odl_pass, ovs_id, bridge_name, port_name):
        '''
        Args:
            ovs_id:
                OVS ID of the bridge        
            bridge_name:
                name of the bridge
            port_name:
                name of the port to be deleted
        '''
        headers = {'Accept': 'application/json'}
        bridge_path = self.odl_bridge_path % (ovs_id, bridge_name)
        url = odl_endpoint +self.odl_config_topology_path + self.odl_ovsdb_topology+ self.odl_node + urllib.parse.quote(bridge_path, safe='') + self.odl_port_path + port_name
        resp = requests.delete(url, headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text
    
    def deleteBridge(self, odl_endpoint, odl_user, odl_pass, ovs_id, bridge_name):
        '''
        Args:
            ovs_id:
                OVS ID of the bridge        
            bridge_name:
                name of the bridge to be deleted
        '''
        headers = {'Accept': 'application/json'}
        bridge_path = self.odl_bridge_path % (ovs_id, bridge_name)
        url = odl_endpoint +self.odl_config_topology_path + self.odl_ovsdb_topology+ self.odl_node + urllib.parse.quote(bridge_path, safe='')
        resp = requests.delete(url, headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text    
    
    def createFlow(self, odl_endpoint, odl_user, odl_pass, jsonFlow, switch_id, flow_id, table_id=0):
        '''
        Create a flow on the switch selected
        Args:
            jsonFlow:
                JSON structure which describes the flow specifications
            switch_id:
                OpenDaylight id of the switch (example: openflow:1234567890)
            flow_id:
                OpenFlow id of the flow
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        '''
        headers = {'Accept': 'application/json', 'Content-type':'application/json'}
        url = odl_endpoint+self.odl_flows_path+self.odl_node+str(switch_id)+(self.odl_flow % table_id)+str(flow_id)
        logging.debug(url+"\n"+jsonFlow)
        resp = requests.put(url,jsonFlow,headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text
    
    def deleteFlow(self, odl_endpoint, odl_user, odl_pass, switch_id, flow_id, table_id=0):
        '''
        Delete a flow
        Args:
            switch_id:
                OpenDaylight id of the switch (example: openflow:1234567890)
            flow_id:
                OpenFlow id of the flow
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        '''
        headers = {'Accept': 'application/json', 'Content-type':'application/json'}
        url = odl_endpoint+self.odl_flows_path+self.odl_node+switch_id+(self.odl_flow % table_id)+str(flow_id)
        logging.debug(url)
        resp = requests.delete(url,headers=headers, auth=(odl_user, odl_pass))
        resp.raise_for_status()
        return resp.text
'''
######################################################################################################
###############################   OpenStack Heat REST calls        ###################################
######################################################################################################
'''
class Heat(object):
    ''' 
    Class (no longer) used to call the Heat Openstack API
    '''
    getStackPath="/stacks"
    createStackPath="/stacks"
    updateStackPath="/stacks/%s/%s"
    deleteStackPath="/stacks/%s/%s"
    getStackIDPath="/stacks/%s"
    stackResourcesPath="/stacks/%s/%s/resources"
    connectSwitchesPath="/connect_switches"
    createPortPath="/create_port"
    createBridgePath="/create_bridge"
    createFlowPath="/create_flow"
    getPortIDPath="/get_port_id"
    
    def getStackList(self, heatEndpoint, token):
        '''
        Return the JSON with the list of the user stacks
        Args:
            heatEndpoint:
                The endpoint to the heat server that should instantiate the stack (example: http://serverAddr:heatport/v1/<tenant-ID>)
            token:
                Keystone token for the authentication
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(heatEndpoint+self.getStackPath, headers=headers)
        resp.raise_for_status()
        return resp.text
        
    def instantiateStack(self, heatEndpoint, token, stackName, jsonStackTemplate, jsonParameters={}):
        '''
        Instantiate the user profile stack from a JSON template in Heat
        Args:
            heatEndpoint:
                The endpoint to the heat server that should instantiate the stack (example: http://serverAddr:heatport/v1/<tenant-ID>)
            stackName:
                Name of the stack to instantiate
            jsonStackTemplate:
                The template in a json format that represents the stack to be instantiated (not the string)
            jsonParameters:
                The JSON data that identify the parameters to input in the stack with the format <param_name>:<param_value> (not the string)
            token:
                Keystone token for the authentication
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        stack_data = {'stack_name': stackName, 'template': jsonStackTemplate, 'parameters': jsonParameters, 'timeout_mins': 60}
        jsondata = json.dumps(stack_data)
        resp = requests.post(heatEndpoint+self.createStackPath, data=jsondata, headers=headers)
        resp.raise_for_status()
        return resp.text
    
    def updateStack(self, heatEndpoint, token, stackName, stackID, jsonStackTemplate, jsonParameters={}):
        '''
        Update the user profile stack from a json template in Heat
        Args:
            heatEndpoint:
                The endpoint to the heat server that should instantiate the stack (example: http://serverAddr:heatport/v1/<tenant-ID>)
            stackName:
                Name of the stack to update
            stackID:
                ID of the stack to update
            jsonStack:
                The template in a JSON format that represents the stack to be instantiated (not the string)
            jsonParameters:
                The JSON data that identify the parameters to input in the stack with the format <param_name>:<param_value> (not the string)
            token:
                Keystone token for the authentication
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        stack_data = {'template': jsonStackTemplate, 'parameters': jsonParameters, 'timeout_mins': 1}
        resp = requests.put(heatEndpoint+(self.updateStackPath % (stackName, stackID)), data=json.dumps(stack_data), headers=headers)
        resp.raise_for_status()
        return resp
    
    def deleteStack(self, heatEndpoint, token, stackName, stackID):
        '''
        Delete the user profile stack
        Args:
            heatEndpoint:
                The endpoint to the heat server that should instantiate the stack (example: http://serverAddr:heatport/v1/<tenant-ID>)
            stackName:
                Name of the stack to update
            stackID:
                ID of the stack to update
            token:
                Keystone token for the authentication
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.delete(heatEndpoint+(self.deleteStackPath % (stackName, stackID)), headers=headers)
        resp.raise_for_status()
        return resp
    
    def getStackID(self, heatEndpoint, token, stackName):
        '''
        Return the ID of the searched stack
        Args:
            heatEndpoint:
                The endpoint to the heat server that should instantiate the stack (example: http://serverAddr:heatport/v1/<tenant-ID>)
            stackName:
                Name of the stack to find
            token:
                Keystone token for the authentication
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(heatEndpoint+(self.getStackIDPath % stackName), headers=headers)
        resp.raise_for_status()
        data = json.loads(resp.text)
        return data['stack']['id']
    
    def getStackStatus(self, heatEndpoint, token, stackName):
        '''
        Return the stack information
        Args:
            heatEndpoint:
                The endpoint to the heat server that should instantiate the stack (example: http://serverAddr:heatport/v1/<tenant-ID>)
            stackName:
                Name of the stack to find
            token:
                Keystone token for the authentication
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(heatEndpoint+(self.getStackIDPath % stackName), headers=headers)
        resp.raise_for_status()
        data = json.loads(resp.text)
        return data['stack']['stack_status']

    def getStackResourcesStatus(self, heatEndpoint, token, stackName, stackID):
        '''
        Return the stack's resources information
        Args:
            heatEndpoint:
                The endpoint to the heat server that should instantiate the stack (example: http://serverAddr:heatport/v1/<tenant-ID>)
            stackName:
                Name of the stack to find
            token:
                Keystone token for the authentication
            stackID:
                ID of the stack 
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(heatEndpoint+(self.stackResourcesPath % (stackName, stackID)), headers=headers)
        resp.raise_for_status()
        data = json.loads(resp.text)
        return data

'''
######################################################################################################
##############################    OpenStack Nova REST calls        ###################################
######################################################################################################
'''
class Nova(object):   
    getFlavorsDetail = "/flavors/detail"
    getHypervisorsPath="/os-hypervisors"
    getHypervisorsInfoPath="/os-hypervisors/detail"
    getAvailabilityZonesPath="/os-availability-zone/detail"
    getHostAggregateListPath="/os-aggregates"
    addComputeNodeToHostAggregatePath = "/os-aggregates/%s/action"
    addServer = "/servers"
    attachInterface = "/servers/%s/os-interface"
    
    def getAvailabilityZones(self, novaEndpoint, token):
        """
        Call usable only for Openstack admin users
        {
          "availabilityZoneInfo": [
            {
              "zoneState": {
                "available": true
              },
              "hosts": {
                "openstack-controller": {
                  "nova-conductor": {
                    "available": true,
                    "active": true,
                    "updated_at": "2015-04-17T09:41:37.000000"
                  },
                  "nova-consoleauth": {
                    "available": true,
                    "active": true,
                    "updated_at": "2015-04-17T09:41:29.000000"
                  },
                  "nova-cert": {
                    "available": true,
                    "active": true,
                    "updated_at": "2015-04-17T09:41:28.000000"
                  },
                  "nova-scheduler": {
                    "available": true,
                    "active": true,
                    "updated_at": "2015-04-17T09:41:33.000000"
                  }
                }
              },
              "zoneName": "internal"
            }
        """
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(novaEndpoint+self.getAvailabilityZonesPath, headers=headers)
        resp.raise_for_status()
        return resp.text
    
    def get_flavors(self, novaEndpoint, token, minRam=None, minDisk=None):
        '''
        Return the flavors data
        Args:
            novaEndpoint:
                The endpoint to the nova server (example: http://serverAddr:novaport/v2/<tenant-ID>)
            token:
                Keystone token for the authentication
            minRam:
                The minimum Ram size of the returned flavors (Optional)
            minDisk:
                The minimum Disk size of the returned flavors (Optional)
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        data = {}
        data['minRam'] = int(minRam or 0)
        data['minDisk'] = int(minDisk or 0)
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(novaEndpoint+self.getFlavorsDetail, params=data, headers=headers)
        resp.raise_for_status()
        flavor = json.loads(resp.text)
        return flavor
    
    def createServer(self, novaEndpoint, token, server_data):
        '''
        Create and instantiate a server and return details
        Args:
            novaEndpoint:
                The endpoint to the nova server (example: http://serverAddr:novaport/v2/<tenant-ID>)
            token:
                Keystone token for the authentication
            server_data:
                JSON structure which describes the server (see http://developer.openstack.org/api-ref-compute-v2.html)
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.post(novaEndpoint + self.addServer, data=json.dumps(server_data), headers=headers)
        resp.raise_for_status()
        return json.loads(resp.text)
    
    def getServerStatus(self, novaEndpoint, token, server_id):
        '''
        Get the status of a specific server (RUNNING, ERROR, etc..)
        Args:
            novaEndpoint:
                The endpoint to the nova server (example: http://serverAddr:novaport/v2/<tenant-ID>)
            token:
                Keystone token for the authentication
            server_id:
                OpenStack internal id of the server
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(novaEndpoint + self.addServer + "/" + server_id, headers=headers)
        resp.raise_for_status()
        data = json.loads(resp.text)
        return data['server']['status']
    
    def deleteServer(self, novaEndpoint, token, server_id):
        '''
        Delete a specific server
        Args:
            novaEndpoint:
                The endpoint to the nova server (example: http://serverAddr:novaport/v2/<tenant-ID>)
            token:
                Keystone token for the authentication
            server_id:
                OpenStack internal id of the server
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.delete(novaEndpoint + self.addServer + "/" + server_id, headers=headers)
        resp.raise_for_status()
        return resp
    
    def attachPort(self, novaEndpoint, token, port_id, server_id):
        data = {"interfaceAttachment": {"port_id": port_id}}
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.post(novaEndpoint + (self.attachInterface % server_id), data=json.dumps(data), headers=headers)
        resp.raise_for_status()
        return json.loads(resp.text)
       
class Glance(object):

    def getImage(self, imageURI, token):
        '''
        Get the image JSON description from the OpenStack URI
        Args:
            imageURI:
                Glance URI of the image (example: "http://server:9292/v2/images/16e08440-5235-4d94-94bf-7a57866b58eb")
            token:
                Keystone token for the authentication
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''         
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(imageURI, headers=headers)
        resp.raise_for_status()
        data = json.loads(resp.text)
        return data

'''
######################################################################################################
##############################    OpenStack Neutron REST calls        ################################
######################################################################################################
'''
class Neutron(object):
    get_networks = "/v2.0/networks"
    get_network_status = "/v2.0/networks/%s"
    create_network = "/v2.0/networks"
    delete_network = "/v2.0/networks/%s"
    create_subnet = "/v2.0/subnets"
    delete_subnet = "/v2.0/subnets/%s"
    get_subnet_status = "/v2.0/subnets/%s"
    get_ports = "/v2.0/ports"
    get_port_status = "/v2.0/ports/%s"
    
    def getNetworks(self, neutronEndpoint, token):
        '''
        Get a JSON list of Neutron networks
        Args:
            neutronEndpoint:
                The endpoint to the neutron server (example: http://serverAddr:neutronport)
            token:
                Keystone token for the authentication
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(neutronEndpoint + self.get_networks, headers=headers)
        resp.raise_for_status()
        return resp.text
    
    def createNetwork(self, neutronEndpoint, token, network_data):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.post(neutronEndpoint + self.create_network, data=json.dumps(network_data), headers=headers)
        resp.raise_for_status()
        return json.loads(resp.text)
    
    def deleteNetwork(self, neutronEndpoint, token, network_id):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.delete(neutronEndpoint + (self.delete_network % network_id), headers=headers)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp
    
    def getNetworkStatus(self, neutronEndpoint, token, network_id):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(neutronEndpoint + (self.get_network_status % network_id), headers=headers)
        if resp.status_code == 404:
            return 'not_found'
        resp.raise_for_status()
        data = json.loads(resp.text)
        return data['network']['status']
    
    def createSubNet(self, neutronEndpoint, token, subnet_data):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.post(neutronEndpoint + self.create_subnet, data=json.dumps(subnet_data), headers=headers)
        resp.raise_for_status()
        return json.loads(resp.text)
    
    def deleteSubNet(self, neutronEndpoint, token, subnet_id):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.delete(neutronEndpoint + (self.delete_subnet %  subnet_id), headers=headers)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp
    
    def getSubNetStatus(self, neutronEndpoint, token, subnet_id):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(neutronEndpoint + (self.get_subnet_status % subnet_id), headers=headers)
        if resp.status_code == 404:
            return 'not_found'
        resp.raise_for_status()
        return 'ACTIVE'
    
    def getPorts(self, neutronEndpoint, token):
        '''
        Get a JSON list of Neutron ports
        Args:
            neutronEndpoint:
                The endpoint to the neutron server (example: http://serverAddr:neutronport)
            token:
                Keystone token for the authentication
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(neutronEndpoint + self.get_ports, headers=headers)
        resp.raise_for_status()
        return resp.text
    
    def createPort(self, neutronEndpoint, token, port_data):
        '''
        Create a Neutron port and return details (JSON)
        Args:
            neutronEndpoint:
                The endpoint to the neutron server (example: http://serverAddr:neutronport)
            token:
                Keystone token for the authentication
            port_data:
                JSON structure which represents the port and its parameters (http://developer.openstack.org/api-ref-networking-v2.html)
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.post(neutronEndpoint + self.get_ports, data=json.dumps(port_data), headers=headers)
        resp.raise_for_status()
        return json.loads(resp.text)
    
    def deletePort(self, neutronEndpoint, token, port_id):
        '''
        Delete a Neutron port
        Args:
            neutronEndpoint:
                The endpoint to the neutron server (example: http://serverAddr:neutronport)
            token:
                Keystone token for the authentication
            port_id:
                OpenStack internal id of the port
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or the token is expired
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.delete(neutronEndpoint + self.get_ports + "/" + port_id, headers=headers)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp
    
    def getPortStatus(self, neutronEndpoint, token, port_id):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': token}
        resp = requests.get(neutronEndpoint + (self.get_port_status % port_id), headers=headers)
        if resp.status_code == 404:
            return 'not_found'
        resp.raise_for_status()
        data = json.loads(resp.text)
        return data['port']['status']

