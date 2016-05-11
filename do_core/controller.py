'''
@author: stefanopetrangeli
'''

import json
import logging
import uuid

from do_core.exception import sessionNotFound, GraphError, StackError
from do_core.nffg_manager import NFFG_Manager
from do_core.sql.session import Session
from do_core.sql.graph import Graph
from do_core.userAuthentication import UserData
from do_core.config import Configuration
from collections import OrderedDict
from sqlalchemy.orm.exc import NoResultFound
from requests.exceptions import HTTPError, ConnectionError


from do_core.authentication import KeystoneAuthentication
from do_core.rest import Glance, Nova, Neutron
from do_core.resources import ProfileGraph, VNF, Endpoint, Net
from do_core.nffg_manager import NFFG_Manager


OPENSTACK_IP = Configuration().OPENSTACK_IP
DEBUG_MODE = Configuration().DEBUG_MODE
OPENSTACK_NETWORKS = Configuration().OPENSTACK_NETWORKS

class OpenstackOrchestratorController(object):
    def __init__(self, user_data):
        '''
        Initialize the OpenstackOrchestratorController
        Args:
            userdata:
                credentials to get Keystone token for the user
        '''
        self.userdata = user_data
        self.num_net = 0
              
    def getAuthTokenAndEndpoints(self):
        #self.node_endpoint = Node().getNode(node.openstack_controller).domain_id # IP Openstack
        #self.compute_node_address = node.domain_id # IP compute node, not needed
        
        self.node_endpoint = OPENSTACK_IP # IP Openstack
        
        self.keystoneEndpoint = 'http://' + self.node_endpoint + ':35357'
        self.token = KeystoneAuthentication(self.keystoneEndpoint, self.userdata.username, self.userdata.password, self.userdata.tenant)
        self.novaEndpoint = self.token.get_endpoint_URL('compute', 'public')
        self.glanceEndpoint = self.token.get_endpoint_URL('image','public')
        self.neutronEndpoint = self.token.get_endpoint_URL('network','public')
        
    def get(self, nffg_id):
        session = Session().get_active_user_session_by_nf_fg_id(nffg_id, error_aware=False)
        logging.debug("Getting session: "+str(session.id))
        graphs_ref = Graph().getGraphs(session.id)
        instantiated_nffgs = []
        for graph_ref in graphs_ref:
            instantiated_nffgs.append(Graph().get_nffg(graph_ref.id))
        
        if not instantiated_nffgs:
            return None
        
        return instantiated_nffgs[0].getJSON()          
        
    def put(self, nf_fg):
        logging.debug('Put from user '+self.userdata.username+" of tenant "+self.userdata.tenant)

        if self.checkNFFGStatus(nf_fg.id) is True:
            logging.debug('NF-FG already instantiated, trying to update it')
            session_id = self.update(nf_fg)
            logging.debug('Update completed')
        else:
            session_id  = uuid.uuid4().hex
            Session().inizializeSession(session_id, self.userdata.getUserID(), nf_fg.id, nf_fg.name)
            
            self.getAuthTokenAndEndpoints()
            
            logging.debug("Forwarding graph: " + nf_fg.getJSON(extended=True))
            try:            
                self.prepareNFFG(nf_fg)
                
                Graph().addNFFG(nf_fg, session_id)

                #Read the nf_fg JSON structure and map it into the proper objects and db entries
                profile_graph = self.buildProfileGraph(nf_fg)
                self.openstackResourcesInstantiation(profile_graph, nf_fg)
                logging.debug("Graph " + profile_graph.id + " correctly instantiated!")
                
                Session().updateStatus(session_id, 'complete')
                
            except Exception as ex:
                logging.exception(ex)
                #Graph().delete_graph(nffg.db_id)
                Session().set_error(session_id)
                raise ex
        
        return session_id
    
    def update(self, nf_fg):
        session = Session().get_active_user_session_by_nf_fg_id(nf_fg.id, error_aware=True)
        Session().updateStatus(session.id, 'updating')

        graphs_ref = Graph().getGraphs(session.id)
        old_nf_fg = Graph().get_nffg(graphs_ref[0].id)

        updated_nffg = old_nf_fg.diff(nf_fg)
        logging.debug("Diff: "+updated_nffg.getJSON(True))
        
        logging.error("Update not yet implemented")
        
        return session.id

        
    def delete(self, nf_fg_id):
        session = Session().get_active_user_session_by_nf_fg_id(nf_fg_id, error_aware=False)
        logging.debug("Deleting session: "+str(session.id))
        
        self.getAuthTokenAndEndpoints()
        
        graphs_ref = Graph().getGraphs(session.id)
        for graph_ref in graphs_ref:
            nffg = Graph().get_nffg(graph_ref.id)
            logging.debug("Forwarding graph: " + nffg.getJSON())
            
            try:
                self.openstackResourcesDeletion(graph_ref.id)
            except Exception as ex:
                logging.exception(ex)
                Session().set_error(session.id)
                raise ex
            
        logging.debug("Graph " + str(nf_fg_id) + " correctly deleted!") 
        logging.debug('Session deleted: '+str(session.id))
        # Set the field ended in the table session to the actual datatime        
        Graph().delete_session(session.id)
        Session().set_ended(session.id)
        
    def checkNFFGStatus(self, service_graph_id):
        try:
            session_id = Session().get_active_user_session_by_nf_fg_id(service_graph_id).id
        except sessionNotFound:
            return False
        
        self.getAuthTokenAndEndpoints()
        status = self.getResourcesStatus(session_id)
        
        if status is None:
            return False
        # If the status of the graph is complete, return False
        if status['status'] == 'complete' or DEBUG_MODE is True:
            return True
        # If the graph is in ERROR.. raise a proper exception
        if status['status'] == 'error':
            raise GraphError("The graph has encountered a fatal error, contact the administrator")
        # TODO:  If the graph is still under instantiation returns 409
        if status['status'] == 'in_progress':
            raise Exception("Graph busy")
        # If the graph is deleted, return True
        if status['status'] == 'ended' or status['status'] == 'not_found':
            return False
        
        
    def getResourcesStatus(self, session_id):
        graphs_ref = Graph().getGraphs(session_id)
        for graph_ref in graphs_ref:
            # TODO: for the moment there is only a graph per session 
            return self.openstackResourcesStatus(graph_ref.id)
        
    def getStatus(self, service_graph_id):
        '''
        Returns the status of the graph
        '''        
        logging.debug("Getting resources information for graph id: "+str(service_graph_id))
        session_id = Session().get_active_user_session_by_nf_fg_id(service_graph_id).id
        logging.debug("Corresponding to session id: "+str(session_id))
        
        self.getAuthTokenAndEndpoints()
        status = self.getResourcesStatus(session_id)
        return json.dumps(status)
        
    def openstackResourcesStatus(self, graph_id):
        token_id = self.token.get_token()
        resources_status = {}
        resources_status['networks'] = {}
        networks = Graph().getNetworks(graph_id)
        for network in networks:
            resources_status['networks'][network.id] = Neutron().getNetworkStatus(self.neutronEndpoint, token_id, network.id)
        resources_status['subnets'] = {}
        subnets = Graph().getSubnets(graph_id)
        for subnet in subnets:
            resources_status['subnets'][subnet.id] = Neutron().getSubNetStatus(self.neutronEndpoint, token_id, subnet.id)
        resources_status['ports'] = {}
        ports = Graph().getPorts(graph_id)
        for port in ports:
            if port.type == 'openstack':
                resources_status['ports'][port.id] = Neutron().getPortStatus(self.neutronEndpoint, token_id, port.internal_id)
        resources_status['vnfs'] = {}
        vnfs = Graph().getVNFs(graph_id)
        for vnf in vnfs:
            resources_status['vnfs'][vnf.id] = Nova().getServerStatus(self.novaEndpoint, token_id, vnf.internal_id)
        
        num_resources = len(resources_status['networks']) + len(resources_status['subnets'])  + len(resources_status['ports']) + len(resources_status['vnfs'])         
        num_resources_completed = 0
        
        for value in resources_status['networks'].values():
            logging.debug("network - "+value)
            if value == 'ACTIVE':
                num_resources_completed = num_resources_completed + 1
        for value in resources_status['subnets'].values():
            logging.debug("subnet - "+value)
            if value == 'ACTIVE':
                num_resources_completed = num_resources_completed + 1
        for value in resources_status['ports'].values():
            logging.debug("port - "+value)
            if value == 'ACTIVE' or value == 'DOWN':
                num_resources_completed = num_resources_completed + 1
        for value in resources_status['vnfs'].values():
            logging.debug("vnf - "+value)
            if value == 'ACTIVE':
                num_resources_completed = num_resources_completed + 1
        
        status  = {}

        logging.debug("num_resources_completed "+str(num_resources_completed))
        logging.debug("num_resources "+str(num_resources))
            
        if num_resources_completed == num_resources:
            status['status'] = 'complete'
            if num_resources != 0:
                status['percentage_completed'] = num_resources_completed/num_resources*100
            else:
                status['percentage_completed'] = 100
        else:
            status['status'] = 'in_progress'
            if num_resources != 0:
                status['percentage_completed'] = num_resources_completed/num_resources*100
        
        return status
    
    def openstackResourcesDeletion(self, graph_id):
        token_id = self.token.get_token()
        vnfs = Graph().getVNFs(graph_id)
        for vnf in vnfs:
            Nova().deleteServer(self.novaEndpoint, token_id, vnf.internal_id)      
        ports = Graph().getPorts(graph_id)
        for port in ports:
            if port.type == "openstack":
                Neutron().deletePort(self.neutronEndpoint, token_id, port.internal_id)
        subnets = Graph().getSubnets(graph_id)
        for subnet in subnets:
            Neutron().deleteSubNet(self.neutronEndpoint, token_id, subnet.id)
        networks = Graph().getNetworks(graph_id)               
        for network in networks:
            Neutron().deleteNetwork(self.neutronEndpoint, token_id, network.id)                               
        
    def openstackResourcesInstantiation(self, profile_graph, nf_fg):
        for network in profile_graph.networks:
            logging.debug("Network: "+json.dumps(network.getNetResourceJSON()))
            network.network_id = Neutron().createNetwork(self.neutronEndpoint, self.token.get_token(), network.getNetResourceJSON())['network']['id']
            # Save the OS network in the db
            Graph().addOSNetwork(network.network_id, network.name)
            logging.debug("SubNet: "+json.dumps(network.getSubNetResourceJSON()))
            network.subnet_id = Neutron().createSubNet(self.neutronEndpoint, self.token.get_token(), network.getSubNetResourceJSON())['subnet']['id']
            Graph().addOSSubNet(network.subnet_id, network.name, network.network_id)
            
        #Instantiate ports and servers directly interacting with Neutron and Nova
        for vnf in profile_graph.functions.values():
            if vnf.status == "new":           
                self.createServer(vnf, nf_fg)
            else:
                for port in vnf.listPort:
                    if port.status == "new":
                        self.addPorttoVNF(port, vnf, nf_fg)
        
                   
        #Create flow on the SDN network for graphs interconnection
        """
        for endpoint in profile_graph.endpoints.values():
            if endpoint.status == "new":
                Graph().setEndpointLocation(self.graph_id, endpoint.id, endpoint.interface)
        """ 
        
        for flowrule in profile_graph.flowrules.values():
            if flowrule.status =='new':
                #TODO: check priority
                if flowrule.match is not None:
                    if flowrule.match.port_in is not None:
                        tmp1 = flowrule.match.port_in.split(':')
                        port1_type = tmp1[0]
                        port1_id = tmp1[1]
                        if port1_type == 'vnf':
                            if len(flowrule.actions) > 1 or flowrule.actions[0].output is None:
                                raise GraphError("Multiple actions or action different from output are not supported between vnfs")
                        elif port1_type == 'endpoint':
                            endpoint_to_vnf = False
                            for action in flowrule.actions:
                                if action.output is not None and action.output.split(':')[0] == "vnf":
                                    endpoint_to_vnf= True
                                    break
                            if endpoint_to_vnf is True:
                                if len(flowrule.actions) > 1:
                                    raise GraphError("Multiple actions are not supported between an endpoint and a vnf")
                                else:
                                    continue
                            endp1 = profile_graph.endpoints[port1_id]
                            """ TODO
                            if endp1.type == 'interface':        
                                self.processFlowrule(endp1, flowrule, profile_graph) 
                            """   
    '''
    ######################################################################################################
    #############################    Resources preparation phase        ##################################
    ######################################################################################################
    '''      
                            
    def prepareNFFG(self, nffg):
        manager = NFFG_Manager(nffg)  
        
        # Retrieve the VNF templates, if a node is a new graph, expand it
        logging.debug('Add templates to nffg')
        manager.addTemplates()
        logging.debug('Post expansion: '+nffg.getJSON())
        
        # Optimize NF-FG, currently the switch VNF when possible will be collapsed
        manager.mergeUselessVNFs()   
        
        # Change the remote node ID in remote_endpoint_id and in prepare_connection_to_remote_endpoint_id to the internal value
        #self.convertRemoteGraphID(nffg)
                                    
    def buildProfileGraph(self, nf_fg):
        profile_graph = ProfileGraph()
        profile_graph.setId(nf_fg.id)
        
        #Remove from the pool of available openstack networks vlans used in endpoints of type vlan
        for endpoint in nf_fg.end_points:
            if endpoint.type == 'vlan':
                if endpoint.vlan_id.isdigit() is False:
                    name = endpoint.vlan_id
                else:                                
                    name = "exp" + str(endpoint.vlan_id)
                if name in OPENSTACK_NETWORKS:              
                    OPENSTACK_NETWORKS.remove(name)
        
        for vnf in nf_fg.vnfs:
            nf = self.buildVNF(vnf)
            profile_graph.addVNF(nf)
        
        for vnf in profile_graph.functions.values():
            self.setVNFNetwork(nf_fg, vnf, profile_graph)

        for endpoint in nf_fg.end_points:
            ep = self.buildEndpoint(endpoint)
            profile_graph.addEndpoint(ep)
        
        for flowrule in nf_fg.flow_rules:
            if flowrule.status is None:
                flowrule.status = 'new'
            profile_graph.addFlowrule(flowrule)
                  
        return profile_graph                        
    
    def buildVNF(self, vnf):
        #Get the necessary info (glance URI and Nova flavor) and create a VNF object
        template = vnf.template
        cpuRequirements = template.cpu_requirements.socket
        logging.debug(template.uri)
        image = Glance().getImage(template.uri, self.token.get_token())
        flavor = self.findFlavor(int(template.memory_size), int(template.root_file_system_size),
            int(template.ephemeral_file_system_size), int(cpuRequirements[0]['coreNumbers']), self.token.get_token())
        if vnf.status is None:
            status = "new"
        else:
            status = vnf.status
        #TODO: add image location to the database
        ##return VNF(vnf.id, vnf, image, flavor, vnf.availability_zone, status)
        return VNF(vnf.id, vnf, image, flavor, "nova", status)
    
    def setVNFNetwork(self, nf_fg, nf, profile_graph):
        for port in nf.ports.values():
            if port.net is None and port.status != 'already_deployed':  
                for flowrule in nf_fg.getFlowRulesSendingTrafficFromPort(nf.id, port.id):
                    logging.debug(flowrule.getDict(True))
                    if flowrule.match is not None:
                        #check if vlan_id is constrained by a local or a remote endpoint
                        for action in flowrule.actions:
                            if action.output is not None:
                                if action.output.split(":")[0] == 'endpoint':
                                    endp = nf_fg.getEndPoint(action.output.split(":")[1])
                                    if endp.type =='vlan' or endp.remote_endpoint_id is not None:
                                        if endp.type =='vlan':
                                            net_vlan = endp.vlan_id
                                        elif endp.remote_endpoint_id is not None:
                                            remote_endp = Graph().get_nffg(endp.remote_endpoint_id.split(':')[0]).getEndPoint(endp.remote_endpoint_id.split(':')[1])
                                            net_vlan = remote_endp.vlan_id
                                        if net_vlan.isdigit() is False:
                                            name = net_vlan
                                        else:                                
                                            name = "exp" + str(net_vlan)
                                        net_id = self.getNetworkIdfromName(name)
                                        port.setNetwork(net_id, net_vlan)                           
                                        networks = Graph().getAllNetworks()
                                        found = False
                                        for net in networks:
                                            if net.id == net_id:
                                                found = True
                                                break
                                        if found is False:
                                            Graph().addOSNetwork(net_id, name, 'complete', net_vlan)
                                        if name in OPENSTACK_NETWORKS:              
                                            OPENSTACK_NETWORKS.remove(name)                                                   
                                        break   
                        #Choose a network arbitrarily (no constraints)    
                        if port.net is None:
                            name, net = self.getNetwork(port, profile_graph)
                            #name, net_id = self.getUnusedNetwork()
                            if name is None:
                                raise StackError("No available network found")
                            port.net = net
                            #Ports sending traffic to this port need to be in the same network
                            for flowrule in nf_fg.getFlowRulesSendingTrafficToPort(nf.id, port.id):
                                if flowrule.match is not None and flowrule.match.port_in is not None and flowrule.match.port_in.split(':')[0] == 'vnf':
                                    tmp = flowrule.match.port_in.split(':', 2)
                                    vnf_id = tmp[1]
                                    port1_id = tmp[2]
                                    port1 = profile_graph.functions[vnf_id].ports[port1_id]
                                    port1.net = net   
                            # TODO: check if this is needed, forse basta fare una insert, se dà eccezione amen       
                            """                       
                            networks = Graph().getAllNetworks()
                            found = False
                            for net in networks:
                                if net.id == net_id:
                                    found = True
                                    break
                            if found is False:
                                Graph().addOSNetwork(net_id, name, 'complete', None) 
                            """
              
                
    def buildEndpoint(self, endpoint):
        if endpoint.status is None:
            status = "new"
        else:
            status = endpoint.status
        """
        if endpoint.remote_endpoint_id is not None:
            delimiter = endpoint.remote_endpoint_id.find(":")
            remote_graph = endpoint.remote_endpoint_id[:delimiter]
            remote_id = endpoint.remote_endpoint_id[delimiter+1:] 
            return Endpoint(endpoint.id, endpoint.name, endpoint.type, endpoint.vlan_id, endpoint.switch_id, endpoint.interface, status, remote_graph, remote_id)
        else:
            return Endpoint(endpoint.id, endpoint.name, endpoint.type, endpoint.vlan_id, endpoint.switch_id, endpoint.interface, status)
        """
        return Endpoint(endpoint.id, endpoint.name, endpoint.type, endpoint.vlan_id, endpoint.node_id, endpoint.interface, status)
    '''
    ######################################################################################################
    ###############################    Interactions with OpenStack       #################################
    ######################################################################################################
    '''
    def createServer(self, vnf, nf_fg):
        for port in vnf.listPort[:]:
            self.createPort(port, vnf, nf_fg) 
        json_data = vnf.getResourceJSON()
        resp = Nova().createServer(self.novaEndpoint, self.token.get_token(), json_data)
        vnf.OSid = resp['server']['id']
        
        #TODO: image location, location, type and availability_zone missing
        Graph().setVNFInternalID(nf_fg.db_id, vnf.id, vnf.OSid, 'complete')
    
    def deleteServer(self, vnf, nf_fg):
        Nova().deleteServer(self.novaEndpoint, self.token.get_token(), vnf.internal_id)
        Graph().deleteFlowRuleFromVNF(vnf.db_id)
        Graph().deleteVNFNetworks(self.graph_id, vnf.db_id)     
        Graph().deletePort(None, self.graph_id, vnf.db_id)
        Graph().deleteVNF(vnf.id, self.graph_id)
        nf_fg.vnfs.remove(vnf)
    
    def createPort(self, port, vnf, nf_fg):
        if port.net is None:
            raise StackError("No network found for this port")
        
        json_data = port.getResourceJSON()      
        resp = Neutron().createPort(self.neutronEndpoint, self.token.get_token(), json_data)
        if resp['port']['status'] == "DOWN":
            port_internal_id = resp['port']['id']
            port.setInternalId(port_internal_id)
            Graph().setPortInternalID(nf_fg.db_id, nf_fg.getVNF(vnf.id).db_id, port.id, port_internal_id, port.status, port_type='openstack')
            Graph().setOSNetwork(port.net, port.id, nf_fg.getVNF(vnf.id).db_id, port_internal_id, nf_fg.db_id)##,  vlan_id = port.vlan)
    
    def deletePort(self, vnf, port, nf_fg): 
        if port.status == 'to_be_deleted':
            Neutron().deletePort(self.neutronEndpoint, self.token.get_token(), port.internal_id)
            Graph().deleteFlowspecFromPort(port.id)
            p = Graph().getPortFromInternalID(port.internal_id, self.graph_id)
            Graph().deleteNetwork(p.os_network_id)
            Graph().deletePort(port.db_id, self.graph_id)
        else:
            # Delete flow-rules associated to that port
            for flowrule in nf_fg.getFlowRulesSendingTrafficFromPort(vnf.id, port.id):
                if flowrule.status == 'to_be_deleted':
                    Neutron().deletePort(self.neutronEndpoint, self.token.get_token(), port.internal_id)                                
                    p = Graph().getPortFromInternalID(port.internal_id, self.graph_id)
                    Graph().deleteNetwork(p.os_network_id)
                    Graph().deletePort(port.db_id, self.graph_id)
                    port.status = 'new'
            '''        
            for flowrule in nf_fg.getFlowRulesSendingTrafficToPort(vnf.id, port.id):
                if flowrule.status == 'to_be_deleted':
                    #check se endpoint o altra vnf per cancellare eventualmetne il flusso o la network sull'altra porta
                    Graph().deleteFlowRule(flowrule.db_id) # toglila
                    """
                    Neutron().deletePort(self.neutronEndpoint, self.token.get_token(), port.internal_id)                                
                    Graph().deleteFlowRule(flowrule.db_id)
                    p = Graph().getPortFromInternalID(port.internal_id)
                    Graph().deleteNetwork(p.os_network_id)
                    Graph().deletePort(port.db_id, self.graph_id)   
                    """                
                    nf_fg.flow_rules.remove(flowrule)
                    #port.status = 'new'                    
            '''
                
    def addPorttoVNF(self, port, vnf, nf_fg):
        vms = Graph().getVNFs(self.graph_id)
        for vm in vms:
            if vm.graph_vnf_id == vnf.id:
                self.createPort(port, vnf, nf_fg)
                Nova().attachPort(self.novaEndpoint, self.token.get_token(), port.internal_id, vm.internal_id)
                break;
            
    def getNetwork(self, port, profile_graph):
        if OPENSTACK_NETWORKS is not None:
            return self.getUnusedNetwork()
        # Create network
        new_net = Net('fakenet_'+str(self.num_net))
        self.num_net += 1
        profile_graph.networks.append(new_net)
        return new_net.name, new_net
        
    def getNetworkIdfromName(self, network_name):
        #Since we need to control explicitly the vlan id of OpenStack networks, we need to use this trick
        #No way to find vlan id from OpenStack REST APIs
        json_data = Neutron().getNetworks(self.neutronEndpoint, self.token.get_token())
        networks = json.loads(json_data)['networks']
        for net in networks:
            if net['name'] == network_name:
                return net['id']
        return None
    
    def getUnusedNetwork(self):
        '''
        Finds an unused openstack network
        '''
        for network in OPENSTACK_NETWORKS[:]:
            network_free = True
            net_id = self.getNetworkIdfromName(network)
            if net_id is not None:
                #Check if there are ports on this network
                json_data = Neutron().getPorts(self.neutronEndpoint, self.token.get_token())
                ports = json.loads(json_data)['ports']
                for port in ports:
                    if port['network_id'] == net_id:
                        network_free = False
                        OPENSTACK_NETWORKS.remove(network)
                        break
                if network_free is False:
                    continue
                OPENSTACK_NETWORKS.remove(network)
                return network, net_id
        return None
    
    
    def findFlavor(self, memorySize, rootFileSystemSize, ephemeralFileSystemSize, CPUrequirements, token):
        '''
        Find the best nova flavor from the given requirements of the machine
        params:
            memorySize:
                Minimum RAM memory required
            rootFileSystemSize:
                Minimum size of the root file system required
            ephemeralFileSystemSize:
                Minimum size of the ephemeral file system required (not used yet)
            CPUrequirements:
                Minimum number of vCore required
            token:
                Keystone token for the authentication
        '''
        flavors = Nova().get_flavors(self.novaEndpoint, token, memorySize, rootFileSystemSize+ephemeralFileSystemSize)['flavors']
        findFlavor = None
        minData = 0
        for flavor in flavors:
            if flavor['vcpus'] >= CPUrequirements:
                if findFlavor == None:
                    findFlavor = flavor
                    minData = flavor['vcpus'] - CPUrequirements + (flavor['ram'] - memorySize)/1024 + flavor['disk'] - rootFileSystemSize - int(ephemeralFileSystemSize or 0)
                elif (flavor['vcpus'] - CPUrequirements + (flavor['ram'] - memorySize)/1024 + flavor['disk'] - rootFileSystemSize - int(ephemeralFileSystemSize or 0)) < minData:
                    findFlavor = flavor
                    minData = flavor['vcpus'] - CPUrequirements + (flavor['ram'] - memorySize)/1024 + flavor['disk'] - rootFileSystemSize - int(ephemeralFileSystemSize or 0)
        return findFlavor      
    

