'''
Created on 13/mag/2015

@author: vida
@author: stefanopetrangeli
'''

import json
import logging


'''
######################################################################################################
#####################       Classes which represent resources into graphs       ######################
######################################################################################################
'''
class VNFTemplate(object):
    def __init__(self, vnf):
        '''
        Constructor for the template
        params:
            vnf:
                JSON structure containing template data
        '''
        self.ports_label = {}
        self.id = vnf.id
        template = vnf.template
        for port in template.ports:
            tmp = int(port.position.split("-")[0])
            self.ports_label[port.label] = tmp

class Port(object):
    '''
    Class that contains the port data for the VNF
    '''    
    def __init__(self, portTemplate, VNFId, status='new'):
        '''
        Constructor for the port
        params:
            portTemplate:
                The template of the port from the user profile graph
            VNFId:
                The Id of the VNF associated to that port
            status:
                useful when updating graphs, can be new, already_present or to_be_deleted
        '''
        self.net = None
        ##self.vlan = None
        self.id = portTemplate.id
        self.VNFId = VNFId
        self.internal_id = None
        self.status = status
        self.type = portTemplate.type
        self.device_id = None
    
    def setNetwork(self, net_id, vlan_id):
        #Network id retrieved through Neutron REST API call
        self.net = net_id
        ##self.vlan = vlan_id
        
    def setDeviceId(self, device_id):
        self.device_id = device_id
    
    def setInternalId(self, internal_id):
        '''
        Set the OpenStack port id to a port object
        Args:
            internal_id:
                Port id returned after port creation with Neutron API
        '''
        self.internal_id = internal_id
    
    def getResourceJSON(self):
        '''
        Get the JSON representation of the port
        '''
        resource = {}
        resource['port'] = {}
        resource['port']['name'] = self.VNFId+self.id
        if type(self.net) is Net:
            self.net = self.net.network_id
        resource['port']['network_id'] = self.net
        if self.device_id is not None:
            resource['port']['device_id'] = self.device_id
        return resource

class VNF(object):
    '''
    Class that contains the VNF data that will be used on the profile generation
    '''
    def __init__(self, VNFId, vnf, image, flavor, availability_zone, status='new'):
        '''
        Constructor for the vnf
        params:
            VNFId:
                The Id of the VNF
            vnf:
                the VNF object extracted from the nf_fg
            image:
                the URI of the image (taken from the Template)
            flavor:
                the flavor which best suits this VNF
            availability_zone:
                the zone where to place it
            status:
                useful when updating graphs, can be new, already_present or to_be_deleted
        '''
        self.availability_zone = availability_zone
        self._id = VNFId
        self.name = vnf.name
        self.ports = {}
        self.listPort = []
        self.flavor = flavor
        self.URIImage = image
        self._OSid = None
        self.status = status
        
        template_info = VNFTemplate(vnf)
        for port in vnf.ports:
            if port.status is None:
                status = "new"
            else:
                status = port.status
            self.ports[port.id] = Port(port, VNFId, status)
            #position = vnf.template.ports[port.id]
            position = template_info.ports_label[port.id.split(":")[0]] + int(port.id.split(":")[1])
            self.listPort.insert(position,self.ports[port.id])
        
    @property
    def id(self):
        return self._id
    
    @property
    def OSid(self):
        return self._OSid
    
    @OSid.setter
    def OSid(self, value):
        self._OSid = value
    
    def getResourceJSON(self):
        '''
        Gets the JSON representation of the VNF
        '''
        resource = {}
        resource['server'] = {}
        resource['server']['name'] = str(self.id)+'-'+str(self.name)
        resource['server']['imageRef'] = self.URIImage['id']
        resource['server']['flavorRef'] = self.flavor['id']
        resource['server']['availability_zone'] = self.availability_zone
        resource['server']['networks'] = []
        
        for port in self.listPort:
            if port.internal_id is not None:
                resource['server']['networks'].append({ "port": port.internal_id})
        return resource

class Endpoint(object):
    def __init__(self, end_id, name, end_type, vlan_id, switch_id, interface, status, remote_graph = None, remote_id = None):
        self.id = end_id
        self.name = name
        self.type = end_type
        self.vlan_id = vlan_id
        self.switch_id = switch_id
        self.interface = interface
        self.status = status
        self.remote_graph = remote_graph
        self.remote_id = remote_id
    
class ProfileGraph(object):
    def __init__(self):
        '''
        Class that stores the profile graph of the user which will be used for Heat template generation
        '''
        self._id = None
        self.functions = {}
        self.endpoints = {}
        self.flowrules = {}
        
        self.networks = []

    
    @property
    def id(self):
        return self._id
    
    def setId(self, profile_id):
        '''
        Set profile id
        '''
        self._id = profile_id
    
    def addVNF(self, vnf):
        '''
        Add a new vnf to the graph
        '''
        self.functions[vnf.id] = vnf
    
    def addEndpoint(self, endpoint):
        '''
        Add a new endpoint to the graph
        '''
        self.endpoints[endpoint.id] = endpoint
        
    def addFlowrule(self, flowrule):
        self.flowrules[flowrule.id] = flowrule
        
class Net(object):
    '''
    Class that contains a network object on the user graph, it contains also the network created for the VM nova constraint
    '''

    def __init__(self, name, subnet="10.0.0.0/24"):
        '''
        Constructor of the network
        '''
        self.name = name
        self.subnet = subnet
        self.dhcp = False
        self.network_id = None
    
    def getNetResourceJSON(self):
        resource = {}
        resource['network'] = {}
        resource['network']['name'] = self.name
        resource['network']['admin_state_up'] = True
        return resource
    
    def getSubNetResourceJSON(self):
        resource = {}
        resource['subnet'] = {}
        resource['subnet']['name'] = 'sub'+self.name
        resource['subnet']['ip_version'] = 4
        resource['subnet']['cidr'] = self.subnet
        resource['subnet']['enable_dhcp'] = self.dhcp
        resource['subnet']['network_id'] = self.network_id
        return resource