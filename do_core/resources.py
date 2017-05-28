'''
@author: vida
@author: stefanopetrangeli
'''

import json
import logging

'''
###############################################################################################################
#####################       Classes which represent resources into graphs for ONOS        #####################
###############################################################################################################
'''
class OnosFlow(object):
    def __init__(self, priority = 5, of_switch_id = None, timeout = 0, actions = None, match = None):
        '''
        Constructor for the Flow
        Args:
            flow_id:
                identifier of the flow (to be recorded for further deletion)
            table_id:
                identifier of the table where to install the flow (in OF1.0 can be only table0!!)
            priority:
                flow priority
            installHw:
                boolean to force installation on the switch (default = True)
            hard_timeout:
                time before flow deletion (default = 0 = no timeout)
            idle_timeout:
                inactivity time before flow deletion (default = 0 = no timeout)
            actions:
                list of Actions for this flow
            match:
                Match for this flow
        '''
        self.priority = priority
        self.timeout = timeout
        self.isPermanent = "true"
        self.of_switch_id = of_switch_id

        self.actions = actions or []
        self.match = match
        
        #self.flow_id = flow_id
        #self.table_id = table_id
        #self.installHw = installHw
        #self.hard_timeout = hard_timeout
        #self.idle_timeout = idle_timeout
    
    def getJSON(self):
        '''
        Gets the JSON.
        '''
        j_flow = {}
        j_list_action = []
        
        
        j_flow[''] = {}
        j_flow['']['priority'] = self.priority
        j_flow['']['timeout'] = self.timeout
        j_flow['']['isPermanent'] = self.isPermanent
        j_flow['']['deviceId'] = self.of_switch_id
        #j_flow['']['strict'] = self.strict
        #j_flow['flow']['id'] = self.flow_id
        #j_flow['flow']['table_id'] = self.table_id

        #j_flow['flow']['installHw'] = self.installHw
        #j_flow['flow']['hard-timeout'] = self.hard_timeout
        #j_flow['flow']['idle-timeout'] = self.idle_timeout
        
        j_flow['']['treatment'] = {}
        j_flow['']['treatment']['instructions'] = {}
        #j_flow['flow']['instructions']['instruction']['order'] = str(0)
        #j_flow['flow']['instructions']['instruction']['apply-actions'] = {}
        
        i = 0
        for action in self.actions:
            j_action = action.getActions(i)
            j_list_action.append(j_action)
            i = i + 1
               
        j_flow['']['treatment']['instructions'] = j_list_action
        
        if (self.match is not None):
            j_flow['']['selector'] = {}
            j_flow['']['selector']['criteria'] = {}
            
            if (self.match.input_port is not None):
                j_flow['']['selector']['criteria']['type'] = "IN_PORT"
                j_flow['']['selector']['criteria']['port'] = self.match.input_port
                
            if (self.match.ip_source is not None):
                j_flow['']['selector']['criteria']['type'] = "IPV4_SRC"
                j_flow['']['selector']['criteria']['ip']   = self.match.ip_source
                
            if (self.match.ip_dest is not None):
                j_flow['']['selector']['criteria']['type'] = "IPV4_DST"
                j_flow['']['selector']['criteria']['ip']   = self.match.ip_dest
                
            if (self.match.ip_protocol is not None):
                j_flow['']['selector']['criteria']['type'] = "IP_PROTO"
                j_flow['']['selector']['criteria']['type'] = self.match.ip_protocol
        
            if (self.match.port_source is not None):
            
                if (self.match.ip_protocol is not None):
                    protocol = self.match.ip_protocol
                    if protocol == "6":
                        #protocol = "tcp"
                        j_flow['']['selector']['criteria']['type'] = "TCP_SRC"
                        j_flow['']['selector']['criteria']['tcpPort'] = self.match.port_source
                        
                    elif protocol == "17":
                        #protocol = "udp"
                        j_flow['']['selector']['criteria']['type'] = "UDP_SRC"
                        j_flow['']['selector']['criteria']['udpPort'] = self.match.port_source
                else:
                    logging.warning('sourcePort discarded. You have to set also the "protocol" field')
        
            if (self.match.port_dest is not None):
                if (self.match.ip_protocol is not None):
                    protocol = self.match.ip_protocol
                    if protocol == "6":
                        #protocol = "tcp"
                        j_flow['']['selector']['criteria']['type'] = "TCP_DST"
                        j_flow['']['selector']['criteria']['tcpPort'] = self.match.port_dest
                        
                    elif protocol == "17":
                        #protocol = "udp"
                        j_flow['']['selector']['criteria']['type'] = "UDP_DST"
                        j_flow['']['selector']['criteria']['udpPort'] = self.match.port_dest
                else:
                    logging.warning('destPort discarded. You have to set also the "protocol" field')
                    
            if (self.match.vlan_id is not None):
            
                j_flow['']['selector']['criteria']['type'] = "VLAN_VID"
                j_flow['']['selector']['criteria']['vlanId'] = self.match.vlan_id
                #j_flow['flow']['match']['vlan-match']['vlan-id']['vlan-id-present'] = self.match.vlan_id_present
                
            if (self.match.eth_match is True):
                
                if (self.match.ethertype is not None):

                    j_flow['']['selector']['criteria']['type'] = "ETH_TYPE"
                    j_flow['']['selector']['criteria']['ethType'] = self.match.ethertype
                    
                if (self.match.eth_source is not None):
                
                    j_flow['']['selector']['criteria']['type'] = "ETH_SRC"
                    j_flow['']['selector']['criteria']['mac']  = self.match.eth_source
                    
                if (self.match.eth_dest is not None):
                
                    j_flow['']['selector']['criteria']['type'] = "ETH_DST"
                    j_flow['']['selector']['criteria']['mac']  = self.match.eth_dest

        return json.dumps(j_flow)
        
class OnosAction(object):
    def __init__(self, action = None):
        '''
        Represents any OpenFlow 1.0 possible action on the outgoing traffic
        '''
        self.address = None
        self.action_type = None
        self.action_subtype = None
        self.action_value = None
        self.output_port = None
        self.max_length = None
        self.vlan_id = None
        self.priority = 0 # priority used to sort actions list
        if action is not None:
            #TODO: add remaining actions
            if action.drop is True:
                self.setDropAction()
            elif action.controller is True:
                self.setControllerAction()
            elif action.set_vlan_id is not None:
                self.setVlanAction(action.set_vlan_id)
            elif action.pop_vlan is True:
                self.setPopVlanAction()
            elif action.set_ethernet_src_address is not None:
                self.setEthernetAddressAction("source", action.set_ethernet_src_address)
            elif action.set_ethernet_dst_address is not None:
                self.setEthernetAddressAction("destination", action.set_ethernet_dst_address)                

    def setEthernetAddressAction(self, _type, address):
        self.address = address
        
        self.action_type = "L2MODIFICATION"
        
        if _type=="source":
            self.action_subtype = "ETH_SRC"
            self.action_value   = address
            
        elif _type=="destination":
            self.action_subtype = "ETH_DST"
            self.action_value   = address

    def setDropAction(self):
        self.action_type = ""
        
    def setPopVlanAction(self):
        self.action_type = "L2MODIFICATION"
        self.action_subtype="VLAN_POP"
        
    def setPushVlanAction(self):
        self.action_type = "L2MODIFICATION"
        self.action_subtype = "VLAN_PUSH"
            
    def setVlanAction(self, vlan_id):
        '''
        Define this action as a vlan tag swapping action
        Args:
            vlan_id:
                vlan id for the new tag
        '''
        self.action_type = "L2MODIFICATION"
        self.action_subtype = "VLAN_ID"
        self.action_value = vlan_id
        
    def setControllerAction(self):
        self.action_type = "OUTPUT"
        self.action_value = "CONTROLLER"
    
    def setOutputAction(self, out_port):
        '''
        Define this action as an output port action
        Args:
            out_port:
                id of the output port where to send out the traffic
        '''
        self.action_type = "OUTPUT"
        self.action_value = out_port
    
    def getActions(self, order):
        '''
        Gets the Action as an object (to be inserted in Flow actions list)
        Args:
            order:
                the order number of this action in the Flow list
        '''
        j_action = {}
        j_action['order'] = order
        
        if self.action_type == "L2MODIFICATION":
        
            j_action['type'] = "L2MODIFICATION"
        
            if self.action_subtype == "ETH_SRC":
                j_action['subtype'] = "ETH_SRC"
                j_action['mac'] = self.action_value
            
            elif self.action_subtype == "ETH_DST":
                j_action['subtype'] = "ETH_DST"
                j_action['mac'] = self.action_value
                
            elif self.action_subtype == "VLAN_POP":
                j_action['subtype'] = "VLAN_POP"
                
            elif self.action_subtype == "VLAN_PUSH":
                j_action['subtype'] = "VLAN_PUSH"
                
            elif self.action_subtype == "VLAN_ID":
                j_action['subtype'] = "VLAN_ID"
                j_action['vlanId']  = self.action_value
        
        elif self.action_type == "OUTPUT":
        
            j_action['type'] = "OUTPUT"
            j_action['port'] = self.action_value

        return j_action

'''
######################################################################################################
#####################       Classes which represent resources into graphs       ######################
######################################################################################################
'''
class Flow(object):
    def __init__(self, flow_id, table_id = 0, priority = 5, installHw = True, 
                 hard_timeout = 0, idle_timeout = 0, actions = None, match = None):
        '''
        Constructor for the Flow
        Args:
            flow_id:
                identifier of the flow (to be recorded for further deletion)
            table_id:
                identifier of the table where to install the flow (in OF1.0 can be only table0!!)
            priority:
                flow priority
            installHw:
                boolean to force installation on the switch (default = True)
            hard_timeout:
                time before flow deletion (default = 0 = no timeout)
            idle_timeout:
                inactivity time before flow deletion (default = 0 = no timeout)
            actions:
                list of Actions for this flow
            match:
                Match for this flow
        '''
        self.strict = False
        self.flow_id = flow_id
        self.table_id = table_id
        self.priority = priority
        self.installHw = installHw
        self.hard_timeout = hard_timeout
        self.idle_timeout = idle_timeout
        
        self.actions = actions or []
        self.match = match
    
    def getJSON(self):
        '''
        Gets the JSON.
        '''
        j_flow = {}
        j_list_action = []
        
        
        j_flow['flow'] = {}
        j_flow['flow']['strict'] = self.strict
        j_flow['flow']['id'] = self.flow_id
        j_flow['flow']['table_id'] = self.table_id
        j_flow['flow']['priority'] = self.priority
        j_flow['flow']['installHw'] = self.installHw
        j_flow['flow']['hard-timeout'] = self.hard_timeout
        j_flow['flow']['idle-timeout'] = self.idle_timeout
        
        j_flow['flow']['instructions'] = {}
        j_flow['flow']['instructions']['instruction'] = {}
        j_flow['flow']['instructions']['instruction']['order'] = str(0)
        j_flow['flow']['instructions']['instruction']['apply-actions'] = {}
        
        i = 0
        for action in self.actions:
            j_action = action.getActions(i)
            j_list_action.append(j_action)
            i = i + 1
               
        j_flow['flow']['instructions']['instruction']['apply-actions']['action'] = j_list_action
        
        if (self.match is not None):
            j_flow['flow']['match'] = {}
            
            if (self.match.input_port is not None):
                j_flow['flow']['match']['in-port'] = self.match.input_port
            if (self.match.ip_source is not None):
                j_flow['flow']['match']['ipv4-source'] = self.match.ip_source
            if (self.match.ip_dest is not None):
                j_flow['flow']['match']['ipv4-destination'] = self.match.ip_dest
            if (self.match.ip_protocol is not None):
                j_flow['flow']['match']['ip-match'] = {}
                j_flow['flow']['match']['ip-match']['ip-protocol'] = self.match.ip_protocol
        
            if (self.match.port_source is not None):
                if (self.match.ip_protocol is not None):
                    protocol = self.match.ip_protocol
                    if protocol == "6":
                        protocol = "tcp"
                    elif protocol == "17":
                        protocol = "udp"
                    j_flow['flow']['match'][protocol+'-source-port'] = self.match.port_source
                else:
                    logging.warning('sourcePort discarded. You have to set also the "protocol" field')
        
            if (self.match.port_dest is not None):
                if (self.match.ip_protocol is not None):
                    protocol = self.match.ip_protocol
                    if protocol == "6":
                        protocol = "tcp"
                    elif protocol == "17":
                        protocol = "udp"
                    j_flow['flow']['match'][protocol+'-destination-port'] = self.match.port_dest
                else:
                    logging.warning('destPort discarded. You have to set also the "protocol" field')
                    
            if (self.match.vlan_id is not None):
                j_flow['flow']['match']['vlan-match'] = {}
                j_flow['flow']['match']['vlan-match']['vlan-id'] = {}
                j_flow['flow']['match']['vlan-match']['vlan-id']['vlan-id'] = self.match.vlan_id
                j_flow['flow']['match']['vlan-match']['vlan-id']['vlan-id-present'] = self.match.vlan_id_present
            if (self.match.eth_match is True):
                j_flow['flow']['match']['ethernet-match'] = {}
                if (self.match.ethertype is not None):
                    j_flow['flow']['match']['ethernet-match']['ethernet-type'] = {}
                    j_flow['flow']['match']['ethernet-match']['ethernet-type']['type'] = self.match.ethertype
                if (self.match.eth_source is not None):
                    j_flow['flow']['match']['ethernet-match']['ethernet-source'] = {}
                    j_flow['flow']['match']['ethernet-match']['ethernet-source']['address'] = self.match.eth_source
                if (self.match.eth_dest is not None):
                    j_flow['flow']['match']['ethernet-match']['ethernet-destination'] = {}
                    j_flow['flow']['match']['ethernet-match']['ethernet-destination']['address'] = self.match.eth_dest

        return json.dumps(j_flow)

class Action(object):
    def __init__(self, action = None):
        '''
        Represents any OpenFlow 1.0 possible action on the outgoing traffic
        '''
        self.address = None
        self.action_type = None
        self.output_port = None
        self.max_length = None
        self.vlan_id = None
        self.vlan_id_present = False
        self.priority = 0 # priority used to sort actions list
        if action is not None:
            #TODO: add remaining actions
            if action.drop is True:
                self.setDropAction()
            elif action.controller is True:
                self.setControllerAction()
            elif action.set_vlan_id is not None:
                self.setVlanAction(action.set_vlan_id)
            elif action.pop_vlan is True:
                self.setPopVlanAction()
            elif action.set_ethernet_src_address is not None:
                self.setEthernetAddressAction("source", action.set_ethernet_src_address)
            elif action.set_ethernet_dst_address is not None:
                self.setEthernetAddressAction("destination", action.set_ethernet_dst_address)                

    def setEthernetAddressAction(self, _type, address):
        self.priority = 4
        self.address = address
        if _type=="source":
            self.action_type = "set-dl-src-action"
        elif _type=="destination":
            self.action_type = "set-dl-dst-action"

    def setDropAction(self):
        self.action_type = "drop-action"
        
    def setPopVlanAction(self):
        self.action_type="pop-vlan-action"
        self.priority = 2
        
    def setControllerAction(self):
        self.action_type = "output-action"
        self.output_port = "CONTROLLER"
        self.max_length = 65535
        self.priority = 9
    
    def setOutputAction(self, out_port, max_length):
        '''
        Define this action as an output port action
        Args:
            out_port:
                id of the output port where to send out the traffic
            max_lenght:
                max length of the packets
        '''
        self.action_type = "output-action"
        self.output_port = out_port
        self.max_length = max_length
        self.priority = 10
    
    def setPushVlanAction(self, ethernet_type=33024):
        self.action_type = "push-vlan-action"
        self.ethernet_type = ethernet_type
        self.priority = 2
            
    def setVlanAction(self, vlan_id):
        '''
        Define this action as a vlan tag swapping action
        Args:
            vlan_id:
                vlan id for the new tag
        '''
        self.action_type = "vlan-match"
        self.vlan_id = vlan_id
        self.vlan_id_present = True
        self.priority = 8
    
    def getActions(self, order):
        '''
        Gets the Action as an object (to be inserted in Flow actions list)
        Args:
            order:
                the order number of this action in the Flow list
        '''
        j_action = {}
        j_action['order'] = order
        
        if self.action_type == "set-dl-src-action":
            j_action['set-dl-src-action'] = {}
            j_action['set-dl-src-action']['address'] = self.address
        elif self.action_type == "set-dl-dst-action":
            j_action['set-dl-dst-action'] = {}
            j_action['set-dl-dst-action']['address'] = self.address
        if self.action_type == "pop-vlan-action":
            j_action['pop-vlan-action'] = {}
        elif self.action_type == "push-vlan-action":
            j_action['push-vlan-action'] = {}
            j_action['push-vlan-action']['ethernet-type'] = self.ethernet_type          
        elif self.action_type == "drop-action":
            j_action['drop-action'] = {}
        elif self.action_type == "output-action":
            j_action['output-action'] = {}
            j_action['output-action']['output-node-connector'] = self.output_port
            j_action['output-action']['max-length'] = self.max_length
        elif self.action_type == "vlan-match":
            j_action['set-field'] = {}
            j_action['set-field']['vlan-match'] = {}
            j_action['set-field']['vlan-match']['vlan-id'] = {}
            j_action['set-field']['vlan-match']['vlan-id']['vlan-id'] = self.vlan_id
            j_action['set-field']['vlan-match']['vlan-id']['vlan-id-present'] = self.vlan_id_present
        
        return j_action
    
class Match(object):
    def __init__(self, match = None):
        '''
        Represents any OpenFlow 1.0 possible matching rules for the incoming traffic
        '''
        self.input_port = None
        self.vlan_id = None
        self.vlan_id_present = None
        self.eth_match = False
        self.ethertype = None
        self.eth_source = None
        self.eth_dest = None
        self.ip_protocol = None
        self.ip_match = None
        self.ip_source = None
        self.ip_dest = None
        self.tp_match = None
        self.port_source = None
        self.port_dest = None
        if match is not None:
            if match.vlan_id is not None:
                self.setVlanMatch(match.vlan_id)
            #if match.vlan_priority is not None:
                #self.VlanPriority(match.vlan_priority)
            if match.ether_type is not None:
                self.setEtherTypeMatch(match.ether_type)
            if match.source_mac is not None or match.dest_mac is not None:
                self.setEthernetMatch(match.source_mac, match.dest_mac)
            if match.source_ip is not None or match.dest_ip is not None:
                self.setIPMatch(match.source_ip, match.dest_ip)
            if match.protocol is not None:
                self.setIPProtocol(match.protocol)
            if match.source_port is not None or match.dest_port is not None:
                self.setTpMatch(match.source_port, match.dest_port)                
                
                #Tos Bits
        
    def setInputMatch(self, in_port):
        '''
        Define this Match as an input port matching
        Args:
            in_port:
                the input port identifier
        '''
        self.input_port = in_port
    
    def setVlanMatch(self, vlan_id):
        '''
        Define this Match as an input port matching
        Args:
            vlan_id:
                the vlan identifier
        '''
        self.vlan_id = vlan_id
        self.vlan_id_present = True
        
    def setEtherTypeMatch(self, ethertype):
        self.eth_match = True
        self.ethertype = ethertype
        
    def setEthernetMatch(self, eth_source = None, eth_dest = None):
        self.eth_match = True
        self.eth_source = eth_source
        self.eth_dest = eth_dest
        
    def setIPProtocol(self, protocol):
        self.ip_protocol = protocol
        
    def setIPMatch(self, ip_source = None, ip_dest = None):
        self.ip_match = True
        self.ip_source = ip_source
        self.ip_dest = ip_dest
        
    def setTpMatch(self, port_source = None, port_dest = None):
        '''
        Sets a transport protocol match
        '''
        self.tp_match = True
        self.port_source = port_source
        self.port_dest = port_dest

    
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
        self.mac = portTemplate.mac
        self.type = portTemplate.type
        self.device_id = None
        self.of_port = None
    
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
        if self.mac is not None:
            resource['port']['mac_address'] = self.mac
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
