'''
@author: stefanopetrangeli
@author: ReliableLion
'''
import json
import logging
import uuid
import time

from do_core.exception import sessionNotFound, GraphError, StackError
from do_core.sql.session import Session
from do_core.sql.graph import Graph
from do_core.config import Configuration
from do_core.authentication import KeystoneAuthentication
from do_core.rest import Glance, Nova, Neutron, ODL
from do_core.resources import ProfileGraph, VNF, Net, Match, Action, Flow, OnosFlow, OnosAction
from do_core.nffg_manager import NFFG_Manager
from do_core.onosBusiness import ONOSBusiness
from do_core.ovsdb import OVSDB

from nffg_library.nffg import FlowRule
from do_core.messaging import Messaging
from do_core.resource_description import ResourceDescription


OPENSTACK_IP = Configuration().OPENSTACK_IP
DEBUG_MODE = Configuration().DEBUG_MODE
JOLNET_MODE = Configuration().JOLNET_MODE
JOLNET_NETWORKS = Configuration().JOLNET_NETWORKS
EXIT_SWITCH = Configuration().EXIT_SWITCH
INTEGRATION_BRIDGE= Configuration().INTEGRATION_BRIDGE
DOMAIN_DESCRIPTION_FILE = Configuration().DOMAIN_DESCRIPTION_FILE
ONOS_ENABLED = Configuration().ONOS_ENABLED
if ONOS_ENABLED is False:
    INTEGRATION_BRIDGE_LOCAL_IP = Configuration().INTEGRATION_BRIDGE_LOCAL_IP
else:
    # This variable is used in case the compute node which hosts a VNF is the same where ONOS is running. In this case
    # the getOvsdbIP method returns the ONOS instance IP that control the br-int, instead of the OVSDB node IP.
    INTEGRATION_BRIDGE_LOCAL_IP = Configuration().ONOS_INTEGRATION_BRIDGE_LOCAL_IP


class OpenstackOrchestratorController(object):
    def __init__(self, user_data):
        '''
        Initialize the OpenstackOrchestratorController
        Args:
            userdata:
                credentials to get Keystone token for the user
        '''
        self.userdata = user_data
        # Num_net needed to create networks and subnets with different names
        self.num_net = 0
        self.res_desc = ResourceDescription(DOMAIN_DESCRIPTION_FILE)

        if ONOS_ENABLED is False:

            self.odlendpoint = "http://" + Configuration().ODL_ADDRESS
            self.odlusername = Configuration().ODL_USERNAME
            self.odlpassword = Configuration().ODL_PASSWORD
            self.ovsdb = OVSDB(self.odlendpoint, self.odlusername, self.odlpassword)

        else:

            self.onosEndpoint = Configuration().ONOS_ADDRESS
            self.onosUsername = Configuration().ONOS_USERNAME
            self.onosPassword = Configuration().ONOS_PASSWORD
            self.onosBusiness = ONOSBusiness(self.onosEndpoint, self.onosUsername, self.onosPassword)
              
    def getAuthTokenAndEndpoints(self):
        self.node_endpoint = OPENSTACK_IP # IP Openstack
        
        self.keystoneEndpoint = 'http://' + self.node_endpoint + ':35357'
        self.token = KeystoneAuthentication(self.keystoneEndpoint, self.userdata.username, self.userdata.password, self.userdata.tenant)
        self.novaEndpoint = self.token.get_endpoint_URL('compute', 'public')
        #self.glanceEndpoint = self.token.get_endpoint_URL('image','public')  # not needed because it is read from the templates
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
                if JOLNET_MODE is False:
                      self.instantiateEndpoints(nf_fg, nf_fg.db_id)
                self.openstackResourcesInstantiation(profile_graph, nf_fg)
                self.instantiateFlowrules(profile_graph, nf_fg.db_id)
                logging.debug("Graph " + profile_graph.id + " correctly instantiated!")
                
                self.res_desc.writeToFile()
                Messaging().publishDomainDescription()
                
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
        
        graph_id = graphs_ref[0].id

        updated_nffg = old_nf_fg.diff(nf_fg)
        logging.debug("Diff: "+updated_nffg.getJSON(extended=True))
                
        try:
            self.openstackResourcesControlledDeletion(updated_nffg, graph_id)
            
            self.prepareNFFG(nf_fg)
            Graph().updateNFFG(updated_nffg, graph_id)
    
            profile_graph = self.buildProfileGraph(updated_nffg)
            if JOLNET_MODE is False:
                  self.instantiateEndpoints(nf_fg, graph_id)
            self.openstackResourcesInstantiation(profile_graph, updated_nffg)
            self.instantiateFlowrules(profile_graph, graph_id)
            
            self.res_desc.writeToFile()
            Messaging().publishDomainDescription()

            logging.debug("Graph " + old_nf_fg.id + " correctly updated!")
            Session().updateStatus(session.id, 'complete')
        
        except Exception as ex:
            logging.exception(ex)
            #Graph().delete_graph(nffg.db_id)
            Session().set_error(session.id)
            raise ex
        
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
                if JOLNET_MODE is False:
                    self.deleteEndpoints(nffg)

                self.res_desc.writeToFile()
                Messaging().publishDomainDescription()
            except Exception as ex:
                logging.exception(ex)
                Session().set_error(session.id)
                raise ex
            
        logging.debug("Graph " + str(nf_fg_id) + " correctly deleted!") 
        logging.debug('Session deleted: '+str(session.id))
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
            # For the moment there is only a graph per session 
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
        flows = Graph().getFlowRules(graph_id)
        for flow in flows:
            if flow.type == "external" and flow.status == "complete":
                if flow.table_id is None:
                    flow.table_id = 0
                if ONOS_ENABLED is False:
                    ODL().deleteFlow(self.odlendpoint, self.odlusername, self.odlpassword, flow.node_id, flow.internal_id, flow.table_id)

                else:
                    self.onosBusiness.deleteFlow(flow.node_id, flow.internal_id)

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
            
    def openstackResourcesControlledDeletion(self, updated_nffg, graph_id):
        # Delete FlowRules
        for flow_rule in updated_nffg.flow_rules[:]:
            if flow_rule.status == 'to_be_deleted':
                self.deleteFlowrule(flow_rule, updated_nffg, graph_id)
                        
        # Delete VNFs
        for vnf in updated_nffg.vnfs[:]:
            if vnf.status == 'to_be_deleted':
                self.deleteVNF(vnf, updated_nffg, graph_id)              
            else:
                # Delete ports
                for port in vnf.ports[:]:
                    if port.status == 'to_be_deleted':
                        self.deletePort(port, graph_id)
                        
        # Delete end-point and end-point resources
        for endpoint in updated_nffg.end_points[:]:
            if endpoint.status == 'to_be_deleted':
                self.deleteEndpoint(endpoint, updated_nffg)
                Graph().deleteEndpoint(endpoint.id, graph_id)
                Graph().deleteEndpointResourceAndResources(endpoint.db_id)
                  
        # Delete unused networks and subnets
        self.deleteUnusedNetworksAndSubnets()  
        
    def deleteFlowrule(self, flowrule, nf_fg, graph_id):    
        flows = Graph().getFlowRule(graph_id, flowrule.id)
        for flow in flows:
            if flow.type == "external" and flow.status == "complete":
                if flow.table_id is None:
                    flow.table_id = 0

                if ONOS_ENABLED is False:
                    ODL().deleteFlow(self.odlendpoint, self.odlusername, self.odlpassword, flow.node_id, flow.internal_id, flow.table_id)

                else:
                    self.onosBusiness.deleteFlow(flow.node_id, flow.internal_id)

                Graph().deleteFlowRule(flow.id)
        Graph().deleteFlowRule(flowrule.db_id)
        nf_fg.flow_rules.remove(flowrule)

    '''
    *********************************
    *    Endpoints deletetion       *
    *********************************
    '''

    def deleteEndpoints(self, nffg):
        for endpoint in nffg.end_points[:]:
            self.deleteEndpoint(endpoint, nffg)

    def deleteEndpoint(self, endpoint, nffg):
        logging.debug("Deleting endpoint type: "+str(endpoint.type))
        if endpoint.type == 'interface' or endpoint.type == 'vlan':
            self.deleteExitEndpoint(nffg, endpoint)
        elif endpoint.type == 'internal':
            self.deleteInternalEndpoint(nffg, endpoint)
        elif endpoint.type == 'gre-tunnel':
            self.deleteGreEndpoint(nffg, endpoint)            
        self.res_desc.deleteEndpoint(endpoint)
        nffg.end_points.remove(endpoint)
        
    def deleteExitEndpoint(self, nffg, endpoint):
        port_to_int_bridge = nffg.id + "-to-" + INTEGRATION_BRIDGE
        port_to_exit_switch =  nffg.id + "-to-" + EXIT_SWITCH
        
        if ONOS_ENABLED is False:
            ovs_id = self.ovsdb.getOVSId(endpoint.node_id)
        
            self.ovsdb.deletePort(ovs_id, port_to_int_bridge, EXIT_SWITCH)
        
            self.ovsdb.deletePort(ovs_id, port_to_exit_switch, INTEGRATION_BRIDGE)

        else:
            ovsdbIP = self.onosBusiness.getOvsdbIP(endpoint.node_id)

            self.onosBusiness.deletePort(ovsdbIP, port_to_int_bridge, EXIT_SWITCH)
    
            self.onosBusiness.deletePort(ovsdbIP, port_to_exit_switch, INTEGRATION_BRIDGE)
            
    def deleteInternalEndpoint(self, nffg, endpoint):
        internal_bridge_id = "br-internal-"+ str(endpoint.internal_group)
        port_to_internal_bridge = nffg.id + "-" + endpoint.id + "-to-" + internal_bridge_id
        port_to_integration_bridge =  nffg.id + "-" + endpoint.id + "-to-" + INTEGRATION_BRIDGE
        
        if ONOS_ENABLED is False:
            ovs_id = self.ovsdb.getOVSId(endpoint.node_id)
        
            self.ovsdb.deletePort(ovs_id, port_to_integration_bridge, internal_bridge_id)
        
            self.ovsdb.deletePort(ovs_id, port_to_internal_bridge, INTEGRATION_BRIDGE)
        
            if len(self.ovsdb.getBridgePorts(ovs_id, internal_bridge_id)) == 1:
                # There are no ports belonging to this bridge so we can delete it
                self.ovsdb.deleteBridge(ovs_id, internal_bridge_id)
                logging.debug("Deleting internal bridge: "+str(internal_bridge_id))

        else:
            ovsdbIP = self.onosBusiness.getOvsdbIP(endpoint.node_id)

            self.onosBusiness.deletePort(ovsdbIP, port_to_integration_bridge, internal_bridge_id)
    
            self.onosBusiness.deletePort(ovsdbIP, port_to_internal_bridge, INTEGRATION_BRIDGE)

            if len(self.onosBusiness.getBridgePorts(endpoint.node_id, internal_bridge_id)) == 1:
                # There are no ports belonging to this bridge so we can delete it
                self.onosBusiness.deleteBridge(endpoint.node_id, ovsdbIP, internal_bridge_id)
                logging.debug("Deleting internal bridge: "+str(internal_bridge_id))

    def deleteGreEndpoint(self, nffg, endpoint):
        gre_port = nffg.id + "-gre-" + endpoint.id
        
        if ONOS_ENABLED is False:

            ovs_id = self.ovsdb.getOVSId(endpoint.local_ip)
                    
            self.ovsdb.deletePort(ovs_id, gre_port, INTEGRATION_BRIDGE)

        else:
            ovsdbIP = self.onosBusiness.getOvsdbIP(endpoint.local_ip)
        
            self.onosBusiness.deleteGreTunnel(ovsdbIP, gre_port, EXIT_SWITCH)

    '''
    *****************************************
    *     Endpoints instantiation     *
    *****************************************
    '''

    def instantiateEndpoints(self, nffg, graph_id):
        for end_point in nffg.end_points[:]:
            if end_point.status == 'new' or end_point.status == 'to_be_updated':
                self.instantiateEndPoint(nffg, end_point, graph_id)
    
    def instantiateEndPoint(self, nffg, end_point, graph_id):
        if end_point.type == "interface" or end_point.type == 'vlan':
            self.manageIngressEndpoint(nffg, end_point, graph_id)    # INTEGRATION_BRIDGE
            # elif end_point.type == 'interface-out' or end_point.type == 'vlan':
            # self.manageExitEndpoint(nffg, end_point)    #EXIT_SWITCH
        elif end_point.type == "internal":
            self.manageInternalEndpoint(nffg, end_point)    # INTERNAL_BRIDGE
        elif end_point.type == "gre-tunnel":
            self.manageGreEndpoint(nffg, end_point, graph_id)        # EXIT_SWITCH

        self.res_desc.addEndpoint(end_point)

    '''
    Managing an endpoint which type is interface
    '''

    def manageIngressEndpoint(self, nffg, ingress_end_point, graph_id):
        port_to_int_bridge = nffg.id + "-to-" + INTEGRATION_BRIDGE
        port_to_exit_switch =  nffg.id + "-to-" + EXIT_SWITCH

        if ONOS_ENABLED is False:
        
            ovs_id = self.ovsdb.getOVSId(ingress_end_point.node_id)

            self.ovsdb.createBridge(ovs_id, EXIT_SWITCH)
            
            self.ovsdb.createPort(ovs_id, ingress_end_point.interface, EXIT_SWITCH)
            
            self.ovsdb.createPatchPort(ovs_id, port_to_int_bridge, EXIT_SWITCH, patch_peer = port_to_exit_switch)
            
            self.ovsdb.createPatchPort(ovs_id, port_to_exit_switch, INTEGRATION_BRIDGE, patch_peer = port_to_int_bridge)
            
            ingress_end_point.interface_internal_id = port_to_exit_switch

        else:

            ovsdbIP = self.onosBusiness.getOvsdbIP(ingress_end_point.node_id)

            self.onosBusiness.createBridge(ovsdbIP, EXIT_SWITCH)
            
            self.onosBusiness.createPort(ovsdbIP, EXIT_SWITCH, ingress_end_point.interface)
            
            self.onosBusiness.createPatchPort(ovsdbIP, EXIT_SWITCH, port_to_int_bridge, patch_peer = port_to_exit_switch)
            
            self.onosBusiness.createPatchPort(ovsdbIP, INTEGRATION_BRIDGE, port_to_exit_switch, patch_peer = port_to_int_bridge)
            
            ingress_end_point.interface_internal_id = port_to_exit_switch


            '''
            #######################################################
            #     Flow from EXIT_SWITCH to INTEGRATION_BRIDGE     #
            #######################################################
            '''

            of_switch_id = self.onosBusiness.getBridgeID(ovsdbIP, EXIT_SWITCH)

            input_port = self.onosBusiness.getOfPort(ovsdbIP, EXIT_SWITCH, False, ingress_end_point.interface)
            match = Match()
            match.setInputMatch(str(input_port))

            actions = []
            output_port = self.onosBusiness.getOfPort(ovsdbIP, EXIT_SWITCH, False, port_to_int_bridge)
            output_action = OnosAction()
            output_action.setOutputAction(str(output_port))
            actions.append(output_action)

            flowj = OnosFlow(priority=50000, of_switch_id=of_switch_id, actions=actions, match=match)
            json_req = flowj.getJSON()

            if DEBUG_MODE is True:
                with open('onos_flow_Endpoint.txt', 'w') as outfile:
                    outfile.write(json_req)
            flow_id = self.onosBusiness.createFlow(json_req)

            flow_rule = FlowRule(_id=nffg.id, node_id=of_switch_id, _type='external', status='complete',
                                 priority=flowj.priority, internal_id=flow_id, table_id=0)
            Graph().addFlowRule(graph_id, flow_rule, None)

            '''
            #######################################################
            #     Flow from INTEGRATION_BRIDGE to EXIT_SWITCH     #
            #######################################################
            '''

            input_port = self.onosBusiness.getOfPort(ovsdbIP, EXIT_SWITCH, False, port_to_int_bridge)
            match = Match()
            match.setInputMatch(str(input_port))

            actions = []
            output_port = self.onosBusiness.getOfPort(ovsdbIP, EXIT_SWITCH, False, ingress_end_point.interface)
            output_action = OnosAction()
            output_action.setOutputAction(str(output_port))
            actions.append(output_action)

            flowj = OnosFlow(priority=50000, of_switch_id=of_switch_id, actions=actions, match=match)
            json_req = flowj.getJSON()

            if DEBUG_MODE is True:
                with open('onos_flow_Endpoint.txt', 'w') as outfile:
                    outfile.write(json_req)
            flow_id = self.onosBusiness.createFlow(json_req)

            flow_rule = FlowRule(_id=nffg.id, node_id=of_switch_id, _type='external', status='complete',
                                 priority=flowj.priority, internal_id=flow_id, table_id=0)
            Graph().addFlowRule(graph_id, flow_rule, None)


            '''
            Managing an endpoint which type is interface-out or vlan

                        
            def manageExitEndpoint(self, nffg, egress_end_point):
                port_to_int_bridge = nffg.id + "-" + egress_end_point.id + "-to-" + INTEGRATION_BRIDGE
                port_to_exit_switch =  nffg.id + "-" + egress_end_point.id + "-to-" + EXIT_SWITCH

                if ONOS_ENABLED is False:
                
                    ovs_id = self.ovsdb.getOVSId(egress_end_point.node_id)

                    self.ovsdb.createBridge(ovs_id, EXIT_SWITCH)
                    
                    self.ovsdb.createPort(ovs_id, EXIT_SWITCH, egress_end_point.interface)
                            
                    self.ovsdb.createPatchPort(ovs_id, EXIT_SWITCH, port_to_int_bridge, patch_peer = port_to_exit_switch)
                    
                    self.ovsdb.createPatchPort(ovs_id, INTEGRATION_BRIDGE, port_to_exit_switch, patch_peer = port_to_int_bridge)        
                    
                    egress_end_point.interface_internal_id =  port_to_exit_switch

                else:

                    ovsdbIP = self.onosBusiness.getOvsdbIP(egress_end_point.node_id)

                    self.onosBusiness.createBridge(ovsdbIP, EXIT_SWITCH)
                    
                    self.onosBusiness.createPort(ovsdbIP, EXIT_SWITCH, egress_end_point.interface, )
                            
                    self.onosBusiness.createPatchPort(ovsdbIP, EXIT_SWITCH, port_to_int_bridge, patch_peer = port_to_exit_switch)
                    
                    self.onosBusiness.createPatchPort(ovsdbIP, INTEGRATION_BRIDGE, port_to_exit_switch, patch_peer = port_to_int_bridge)        
                    
                    egress_end_point.interface_internal_id =  port_to_exit_switch

            '''

            '''
            Managing an endpoint which type is internal
            '''
        
    def manageInternalEndpoint(self, nffg, internal_end_point):
        if internal_end_point.node_id is None:
            raise Exception("Endpoint "+ internal_end_point.id + " must specify the compute node address in the node-id field")
        internal_bridge_id = "br-internal-"+ str(internal_end_point.internal_group)
        port_to_internal_bridge = nffg.id + "-" + internal_end_point.id + "-to-" + internal_bridge_id
        port_to_integration_bridge =  nffg.id + "-" + internal_end_point.id + "-to-" + INTEGRATION_BRIDGE

        if ONOS_ENABLED is False:
        
            ovs_id = self.ovsdb.getOVSId(internal_end_point.node_id)

            self.ovsdb.createBridge(ovs_id, internal_bridge_id)
                    
            self.ovsdb.createPatchPort(ovs_id, port_to_integration_bridge, internal_bridge_id, patch_peer = port_to_internal_bridge)
            
            self.ovsdb.createPatchPort(ovs_id, port_to_internal_bridge, INTEGRATION_BRIDGE, patch_peer = port_to_integration_bridge)
            
            internal_end_point.interface_internal_id = port_to_internal_bridge

        else:

            ovsdbIP = self.onosBusiness.getOvsdbIP(internal_end_point.node_id)

            self.onosBusiness.createBridge(ovsdbIP, internal_bridge_id)
                    
            self.onosBusiness.createPatchPort(ovsdbIP, internal_bridge_id, port_to_integration_bridge, patch_peer = port_to_internal_bridge)
            
            self.onosBusiness.createPatchPort(ovsdbIP, INTEGRATION_BRIDGE, port_to_internal_bridge, patch_peer = port_to_integration_bridge)
            
            internal_end_point.interface_internal_id = port_to_internal_bridge

    '''
    #####################################################
    #   Managing an endpoint which type is gre-tunnel   #
    #####################################################
    '''
        
    def manageGreEndpoint(self, nffg, gre_end_point, graph_id):
        gre_port = nffg.id + "-gre-" + gre_end_point.id
        port_to_int_bridge = nffg.id + "-to-" + INTEGRATION_BRIDGE
        port_to_exit_switch = nffg.id + "-to-" + EXIT_SWITCH

        if ONOS_ENABLED is False:
        
            ovs_id = self.ovsdb.getOVSId(gre_end_point.local_ip)
                            
            self.ovsdb.createGrePort(ovs_id, gre_port, INTEGRATION_BRIDGE, gre_end_point.local_ip, gre_end_point.remote_ip, gre_end_point.gre_key)
            
            gre_end_point.interface_internal_id = gre_port
            # This is needed in order to uniform the processFlowrule function regardless of the endpoint type
            gre_end_point.node_id = gre_end_point.local_ip

        else:

            ovsdbIP = self.onosBusiness.getOvsdbIP(gre_end_point.local_ip)
                            
            self.onosBusiness.createGreTunnel(ovsdbIP, EXIT_SWITCH, gre_port, gre_end_point.local_ip, gre_end_point.remote_ip, gre_end_point.gre_key)

            self.onosBusiness.createPatchPort(ovsdbIP, EXIT_SWITCH, port_to_int_bridge,
                                              patch_peer=port_to_exit_switch)

            self.onosBusiness.createPatchPort(ovsdbIP, INTEGRATION_BRIDGE, port_to_exit_switch,
                                              patch_peer=port_to_int_bridge)

            # This variable identifies the patch port on the INTEGRATION_BRIDGE which receives the traffic
            gre_end_point.interface_internal_id = port_to_exit_switch

            # This is needed in order to uniform the processFlowrule function regardless of the endpoint type
            gre_end_point.node_id = gre_end_point.local_ip

            '''
            #######################################################
            #     Flow from EXIT_SWITCH to INTEGRATION_BRIDGE     #
            #######################################################
            '''

            of_switch_id = self.onosBusiness.getBridgeID(ovsdbIP, EXIT_SWITCH)

            input_port = self.onosBusiness.getOfPort(ovsdbIP, EXIT_SWITCH, False, gre_port)
            match = Match()
            match.setInputMatch(str(input_port))

            actions = []
            output_port = self.onosBusiness.getOfPort(ovsdbIP, EXIT_SWITCH, False, port_to_int_bridge)
            output_action = OnosAction()
            output_action.setOutputAction(str(output_port))
            actions.append(output_action)

            flowj = OnosFlow(priority=50000, of_switch_id=of_switch_id, actions=actions, match=match)
            json_req = flowj.getJSON()

            if DEBUG_MODE is True:
                with open('onos_flow_Endpoint.txt', 'w') as outfile:
                    outfile.write(json_req)
            flow_id = self.onosBusiness.createFlow(json_req)

            flow_rule = FlowRule(_id=nffg.id, node_id=of_switch_id, _type='external', status='complete',
                                 priority=flowj.priority, internal_id=flow_id, table_id=0)
            Graph().addFlowRule(graph_id, flow_rule, None)

            '''
            #######################################################
            #     Flow from INTEGRATION_BRIDGE to EXIT_SWITCH     #
            #######################################################
            '''

            input_port = self.onosBusiness.getOfPort(ovsdbIP, EXIT_SWITCH, False, port_to_int_bridge)
            match = Match()
            match.setInputMatch(str(input_port))

            actions = []
            output_port = self.onosBusiness.getOfPort(ovsdbIP, EXIT_SWITCH, False, gre_port)
            output_action = OnosAction()
            output_action.setOutputAction(str(output_port))
            actions.append(output_action)

            flowj = OnosFlow(priority=50000, of_switch_id=of_switch_id, actions=actions, match=match)
            json_req = flowj.getJSON()

            if DEBUG_MODE is True:
                with open('onos_flow_Endpoint.txt', 'w') as outfile:
                    outfile.write(json_req)
            flow_id = self.onosBusiness.createFlow(json_req)

            flow_rule = FlowRule(_id=nffg.id, node_id=of_switch_id, _type='external', status='complete',
                                 priority=flowj.priority, internal_id=flow_id, table_id=0)
            Graph().addFlowRule(graph_id, flow_rule, None)

    '''
    *********************************************************
    *     Instantiation of resources within OpenStack       *
    *********************************************************
    '''
        
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
                        self.addPortToVNF(port, vnf, nf_fg)
        
        for endpoint in profile_graph.endpoints.values():
            if endpoint.status == "new":
                Graph().setEndpointLocation(nf_fg.db_id, endpoint.id, endpoint.interface)

    '''
    ********************************************
    *         Flow Rules Management            *
    ********************************************
    '''
                                
    def instantiateFlowrules(self, profile_graph, graph_id):
        if JOLNET_MODE is False:
            # Wait for VNFs being up, then instantiate flows
            logging.info ("The domain orchestrator is waiting for VNF(s) being up. This may took some minutes...")
            while True:
                complete = True
                resources_status = {}
                resources_status['vnfs'] = {}
                """
                resources_status['ports'] = {}
                ports = Graph().getPorts(graph_id)
                for port in ports:
                    if port.type == 'openstack':
                        resources_status['ports'][port.id] = Neutron().getPortStatus(self.neutronEndpoint, self.token.get_token(), port.internal_id)
                """
                vnfs = Graph().getVNFs(graph_id)
                for vnf in vnfs:
                    resources_status['vnfs'][vnf.internal_id] = Nova().getServerStatus(self.novaEndpoint, self.token.get_token(), vnf.internal_id)
                for value in resources_status['vnfs'].values():
                    if value == 'ERROR':
                        raise StackError("At least one VNF is in ERROR state")
                    if value != 'ACTIVE':
                        complete = False
                if complete is True:
                    break
                time.sleep(1)
                #print("sleep")
            
            for flowrule in profile_graph.flowrules.values():
                if flowrule.status =='new':
                    self.instantiateFlowrule(profile_graph, graph_id, flowrule)

    '''
    If one of this methods are called it means that all the resources have been instantiated within OpenStack
    '''
                
    def instantiateFlowrule(self, profile_graph, graph_id, flowrule):
        # Only flowrules that involve a VNF and an endpoint are installed
        if flowrule.match.port_in is not None:
            tmp1 = flowrule.match.port_in.split(':',1)
            port1_type = tmp1[0]
            #port1_id = tmp1[1]
            if port1_type == 'vnf':
                if len(flowrule.    actions) > 1 or flowrule.actions[0].output is None:
                    raise GraphError("Multiple actions or action different from output are not supported")
                action = flowrule.actions[0]
                if action.output.split(':')[0] == "endpoint":
                    self.processFlowrule(profile_graph, graph_id, flowrule)
                else:
                    self.processFlowrule(profile_graph, graph_id, flowrule)
                    # output is vnf: vnf to vnf
                    if flowrule.match.isComplex() is True:
                        logging.warning("Complex flowrules between VNFs are not supported and the additional fields have been discarded. You can specify only 'port_in' in match")
            elif port1_type == 'endpoint':
                for action in flowrule.actions:
                    if action.output is not None and action.output.split(':')[0] == "vnf":
                        self.processFlowrule(profile_graph, graph_id, flowrule)
                        
    def processFlowrule(self, profile_graph, graph_id, flowrule):
        # Max flowrule priority within ONOS is 65535, and those flow are deployed with a priority >= 50000; otherwise
        # they are ignored by ONOS in favor of its flows
        if flowrule.priority > 15535:
            logging.warning("Flowrule priority cannot be greater than 16382 because it could break the "+ INTEGRATION_BRIDGE + " operation")
            flowrule.priority = 15534

        matchPort = flowrule.match.port_in.split(':', 2)
        port1_type = matchPort[0]
        port1_id = matchPort[1]

        '''
        #################################################################
        #   Is the port_in traffic coming from a VNF or an endpoint?    # 
        #################################################################
        '''
        if port1_type == "vnf":
            '''
                FROM A VNF 
            ''' 
            vnf_portOut = None
            vnf = profile_graph.functions[port1_id]
            vnf_port = vnf.ports[matchPort[2]]
            endpoint = None
            match = Match(flowrule.match)

            for action in flowrule.actions:
                if action.output is not None and action.output.split(':')[0] == "endpoint":
                    endpoint = profile_graph.endpoints[action.output.split(':')[1]]
                    break
                if action.output is not None and action.output.split(':')[0] == "vnf":
                    output = action.output.split(':',2)
                    vnfOut = profile_graph.functions[output[1]]
                    vnf_portOut = vnfOut.ports[output[2]]
                    break

            '''
                Get the OF device id to which the relative VNF or endpoint belong to. In case of an
                endpoint, the device id is always the br-int ID because the traffic will be forwarded to
                the patch port connected to the bridge with that endpoint.
            '''
            if endpoint is not None:

                if ONOS_ENABLED is False:

                    ovs_id = self.ovsdb.getOVSId(endpoint.node_id)
                    of_switch_id = self.getOpenFlowSwitchID(ovs_id, INTEGRATION_BRIDGE)

                else:

                    ovsdbIP = self.onosBusiness.getOvsdbIP(endpoint.node_id)
                    of_switch_id = self.onosBusiness.getBridgeID(ovsdbIP, INTEGRATION_BRIDGE)

            else:

                if ONOS_ENABLED is False:

                    ovs_id = self.ovsdb.getOVSId(INTEGRATION_BRIDGE_LOCAL_IP)
                    of_switch_id = self.getOpenFlowSwitchID(ovs_id, INTEGRATION_BRIDGE)

                else:

                    vnf_bridge_id = self.onosBusiness.getHostBridgeID(vnf_port.internal_id[0:11])
                    ovsdbIP = self.onosBusiness.getBridgeOvsdbNodeIP(vnf_bridge_id)

                    try:
                        of_switch_id = self.onosBusiness.getBridgeID(ovsdbIP, INTEGRATION_BRIDGE)
                        # ovsdbIP = self.onosBusiness.getOvsdbIP(INTEGRATION_BRIDGE_LOCAL_IP)

                        # of_switch_id = self.onosBusiness.getBridgeID(ovsdbIP, INTEGRATION_BRIDGE)
                    except:
                        of_switch_id = self.onosBusiness.getBridgeID(INTEGRATION_BRIDGE_LOCAL_IP, INTEGRATION_BRIDGE)

            '''
                    Get the VNF port which match the port_in criteria
            '''

            if vnf_port.of_port is None:

                if ONOS_ENABLED is False:

                    input_port = self.ovsdb.getOfPort(ovs_id, INTEGRATION_BRIDGE, vnf_port.internal_id[0:8])
                    vnf_port.of_port = str(input_port)

                else:

                    # Get the ovsdb node IP where the input VNF is located
                    VNFBridgeID = self.onosBusiness.getHostBridgeID(vnf_port.internal_id[0:11])
                    ovsdbIPVNF  = self.onosBusiness.getBridgeOvsdbNodeIP(VNFBridgeID)

                    try:
                        # Input port is returned as a number which identifies the port within that bridge
                        input_port = self.onosBusiness.getOfPort(ovsdbIPVNF, INTEGRATION_BRIDGE, True, vnf_port.internal_id[0:11])
                    except:
                        tempIP = self.onosBusiness.getOvsdbIP(INTEGRATION_BRIDGE_LOCAL_IP)
                        input_port = self.onosBusiness.getOfPort(tempIP, INTEGRATION_BRIDGE, True, vnf_port.internal_id[0:11])
                    vnf_port.of_port = str(input_port)

            match.setInputMatch(vnf_port.of_port)

            '''
            ########################################
            #   Now it's time to get the actions   #
            ########################################
            '''

            actions = []
            if endpoint is not None and endpoint.type == "vlan":

                if ONOS_ENABLED is False:
                    push_vlan_action = Action()
                    push_vlan_action.setPushVlanAction()
                    set_vlan_action = Action()
                    set_vlan_action.setVlanAction(endpoint.vlan_id)
                    actions.append(push_vlan_action)
                    actions.append(set_vlan_action)
                    
                else:
                    
                    push_vlan_action = OnosAction()
                    push_vlan_action.setPushVlanAction()
                    set_vlan_action = OnosAction()
                    set_vlan_action.setVlanAction(endpoint.vlan_id)
                    actions.append(push_vlan_action)
                    actions.append(set_vlan_action)
                
            if endpoint is not None:

                '''
                    It's a VNF-Endpoint flow
                '''
            
                if ONOS_ENABLED is False:
                
                    output_port = self.ovsdb.getOfPort(ovs_id, INTEGRATION_BRIDGE, False, endpoint.interface_internal_id)
                    output_action = Action()
                    output_action.setOutputAction(str(output_port), 65535)
                    actions.append(output_action)
                    
                else:

                    '''
                    #####################################################################################
                    #       Check if the endpoint and the VNF are on the same compute node or not       #
                    #####################################################################################
                    '''

                    # Get the ovsdb node IP where the input VNF is located
                    VNFBridgeID = self.onosBusiness.getHostBridgeID(vnf_port.internal_id[0:11])
                    ovsdbIPVNF  = self.onosBusiness.getBridgeOvsdbNodeIP(VNFBridgeID)


                    if endpoint.node_id != ovsdbIPVNF and ONOS_ENABLED is True:
                        '''
                            The endpoint and the VNF are on different compute nodes
                        '''

                        # Create GRE tunnel
                        # Flow from VNF to GRE endpoint
                        # Flow from GRE endpoint2 to endpoint

                        gre_port = graph_id + "-gre-" + endpoint.node_id

                        # Endpoint 1 it's the compute node that hosts the endpoint
                        endpoint1 = ovsdbIPVNF

                        # Endpoint 2 it's the compute node that hosts the VNF
                        endpoint2 = self.onosBusiness.getOvsdbIP(endpoint.node_id)

                        self.onosBusiness.createGreTunnel(endpoint1, INTEGRATION_BRIDGE, gre_port, endpoint1, endpoint2,
                                                          graph_id)
                        self.onosBusiness.createGreTunnel(endpoint2, INTEGRATION_BRIDGE, gre_port, endpoint2, endpoint1,
                                                          graph_id)

                        output_port = self.onosBusiness.getOfPort(endpoint1, INTEGRATION_BRIDGE, False, gre_port)
                        output_action = OnosAction()
                        output_action.setOutputAction(str(output_port))
                        actions.append(output_action)

                        '''
                        ###############################
                        #        Flow Creation        #
                        ###############################
                        '''

                        flowj = OnosFlow(priority=50000+flowrule.priority, of_switch_id=of_switch_id, actions=actions,
                                         match=match)
                        json_req = flowj.getJSON()

                        if DEBUG_MODE is True:
                            with open('onos_flow_Endpoint.txt', 'w') as outfile:
                                outfile.write(json_req)
                        flow_id = self.onosBusiness.createFlow(json_req)
                        
                        flow_rule = FlowRule(_id=flowrule.id, node_id=of_switch_id, _type='external', status='complete',
                                             priority=flowj.priority, internal_id=flow_id, table_id=0)

                        Graph().addFlowRule(graph_id, flow_rule, None)

                        '''
                            SECOND ENDPOINT
                        '''

                        of_switch_id = self.onosBusiness.getBridgeID(endpoint2, INTEGRATION_BRIDGE)
                        input_port = self.onosBusiness.getOfPort(endpoint2, INTEGRATION_BRIDGE, False, gre_port)

                        match.setInputMatch(str(input_port))

                        # [0:11] because internal_id will be like tapXXXXXXXX-XX
                        output_port = self.onosBusiness.getOfPort(endpoint2, INTEGRATION_BRIDGE, False, endpoint.internal_id)

                        output_action = OnosAction()
                        output_action.setOutputAction(str(output_port))
                        actions.append(output_action)

                        flowj = OnosFlow(priority=50000+flowrule.priority, of_switch_id=of_switch_id, actions=actions,
                                         match=match)
                        json_req = flowj.getJSON()

                        if DEBUG_MODE is True:
                            with open('onos_flow_Endpoint.txt', 'w') as outfile:
                                outfile.write(json_req)
                        flow_id = self.onosBusiness.createFlow(json_req)
                        
                        flow_rule = FlowRule(_id=flowrule.id, node_id=of_switch_id, _type='external', status='complete',
                                             priority=flowj.priority, internal_id=flow_id, table_id=0)

                        Graph().addFlowRule(graph_id, flow_rule, None)
                    
                    else:

                        '''
                            The endpoint and the VNF are on the same compute node
                        '''

                        print("Same compute Node: " + endpoint.interface_internal_id + " IP: " + ovsdbIP)
                        output_port = self.onosBusiness.getOfPort(ovsdbIP, INTEGRATION_BRIDGE, False,
                                                                  endpoint.interface_internal_id)
                        output_action = OnosAction()
                        output_action.setOutputAction(str(output_port))
                        actions.append(output_action)

                        '''
                        ###############################
                        #        Flow Creation        #
                        ###############################
                        '''

                        flowj = OnosFlow(priority=50000 + flowrule.priority, of_switch_id=of_switch_id, actions=actions,
                                         match=match)
                        json_req = flowj.getJSON()

                        if DEBUG_MODE is True:
                            with open('onos_flow_Endpoint.txt', 'w') as outfile:
                                outfile.write(json_req)
                        flow_id = self.onosBusiness.createFlow(json_req)

                        flow_rule = FlowRule(_id=flowrule.id, node_id=of_switch_id, _type='external', status='complete',
                                             priority=flowj.priority, internal_id=flow_id, table_id=0)
                        Graph().addFlowRule(graph_id, flow_rule, None)
                
            else:

                '''
                    It's a VNF-VNF flow
                '''

                if vnf_portOut.of_port is None:
                    if ONOS_ENABLED is False:
                    
                       out_port = self.ovsdb.getOfPort(ovs_id, INTEGRATION_BRIDGE, vnf_portOut.internal_id[0:8])
                       vnf_portOut.of_port = str(out_port)
                       
                    else:

                        try:
                            out_port = self.onosBusiness.getOfPort(ovsdbIP, INTEGRATION_BRIDGE, True,
                                                                   vnf_portOut.internal_id[0:11])
                        except:
                            out_port = self.onosBusiness.getOfPort(INTEGRATION_BRIDGE_LOCAL_IP, INTEGRATION_BRIDGE, True,
                                                                   vnf_portOut.internal_id[0:11])

                        # Input port is returned as a number which identify the port within that bridge
                        vnf_portOut.of_port = str(out_port)

                if ONOS_ENABLED is False:
                    output_action = Action()
                    output_action.setOutputAction(vnf_portOut.of_port, 65535)
                    actions.append(output_action)

                else:
                    output_action = OnosAction()
                    output_action.setOutputAction(vnf_portOut.of_port)
                    actions.append(output_action)

                '''
                *******************************
                *        Flow Creation        *
                *******************************
                '''

                if ONOS_ENABLED is False:

                    flow_id = str(profile_graph.id) + "_" + str(flowrule.id)

                    flowj = Flow(flow_id, table_id=0, priority=16385+flowrule.priority, actions=actions, match=match)
                    json_req = flowj.getJSON()
                    #print (json_req)

                    ODL().createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, of_switch_id,
                                     flow_id, flowj.table_id)

                else:

                    flowj = OnosFlow(priority=50000+flowrule.priority, of_switch_id=of_switch_id, actions=actions,
                                     match=match)
                    json_req = flowj.getJSON()

                    if DEBUG_MODE is True:
                        with open('onos_flow_Endpoint.txt', 'w') as outfile:
                            outfile.write(json_req)
                    flow_id = self.onosBusiness.createFlow(json_req)

                flow_rule = FlowRule(_id=flowrule.id, node_id=of_switch_id, _type='external', status='complete',
                                     priority=flowj.priority, internal_id=flow_id, table_id=0)

                Graph().addFlowRule(graph_id, flow_rule, None)

                if ONOS_ENABLED is False:

                    flow_id = str(profile_graph.id) + "_" + str(flowrule.id)

                    flowj = Flow(flow_id, table_id=110, priority=16385+flowrule.priority, actions=actions, match=match)
                    json_req = flowj.getJSON()
                    print (json_req)

                    ODL().createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, of_switch_id, flow_id, flowj.table_id)

                    flow_rule = FlowRule(_id=flowrule.id,node_id=of_switch_id,_type='external', status='complete',
                                         priority=flowj.priority, internal_id=flow_id, table_id=110)

                    Graph().addFlowRule(graph_id, flow_rule, None)

        elif port1_type == "endpoint":

            '''
            #########################################################################
            #   Is the port_in traffic coming from a VNF or an endpoint? Endpoint   #
            #########################################################################
            ''' 

            endpoint = profile_graph.endpoints[port1_id]
            endpoint_out = None
            match = Match(flowrule.match)

            for action in flowrule.actions:
            
                if action.output is not None and action.output.split(':')[0] == "vnf":
                    output = action.output.split(':', 2)
                    vnf = profile_graph.functions[output[1]]
                    vnf_port = vnf.ports[output[2]]
                    break

                if action.output is not None and action.output.split(':')[0] == "endpoint":
                    endpoint_out = profile_graph.endpoints[action.output.split(':')[1]]
                    break

            if ONOS_ENABLED is False:

                ovs_id = self.ovsdb.getOVSId(endpoint.node_id)
                of_switch_id = self.getOpenFlowSwitchID(ovs_id, INTEGRATION_BRIDGE)

                input_port = self.ovsdb.getOfPort(ovs_id, INTEGRATION_BRIDGE, endpoint.interface_internal_id)

            else:
            
                ovsdbIP = self.onosBusiness.getOvsdbIP(endpoint.node_id)
                of_switch_id = self.onosBusiness.getBridgeID(ovsdbIP, INTEGRATION_BRIDGE)

                print("I'm in controller row: 1143" + endpoint.interface_internal_id)

                input_port = self.onosBusiness.getOfPort(ovsdbIP, INTEGRATION_BRIDGE, False,
                                                         endpoint.interface_internal_id)

            match.setInputMatch(str(input_port))

            actions = []
            if endpoint.type == "vlan":

                if ONOS_ENABLED is False:
                    match.setVlanMatch(endpoint.vlan_id)
                    pop_vlan_action = Action()
                    pop_vlan_action.setPopVlanAction()
                    actions.append(pop_vlan_action)

                else:

                    match.setVlanMatch(endpoint.vlan_id)
                    pop_vlan_action = OnosAction()
                    pop_vlan_action.setPopVlanAction()
                    actions.append(pop_vlan_action)
                
            if endpoint_out is not None:

                '''
                    It's a Endpoint-Endpoint flow
                '''
            
                output_port = self.onosBusiness.getOfPort(ovsdbIP, INTEGRATION_BRIDGE, False,
                                                          endpoint_out.interface_internal_id)
                output_action = OnosAction()
                output_action.setOutputAction(str(output_port))
                actions.append(output_action)

                '''
                ###############################
                #        Flow Creation        #
                ###############################
                '''
                if ONOS_ENABLED is False:

                    flow_id = str(profile_graph.id) + "_" + str(flowrule.id) 

                    flowj = Flow(flow_id, table_id=0, priority=16385+flowrule.priority, actions=actions, match=match)
                    json_req = flowj.getJSON()
                    # print (json_req)

                    ODL().createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, of_switch_id,
                                     flow_id, flowj.table_id)

                else:

                    flowj = OnosFlow(priority=50000+flowrule.priority, of_switch_id=of_switch_id, actions=actions,
                                     match=match)
                    json_req = flowj.getJSON()

                    if DEBUG_MODE is True:
                        with open('onos_flow_Endpoint.txt', 'w') as outfile:
                            outfile.write(json_req)
                    flow_id = self.onosBusiness.createFlow(json_req)
                
                flow_rule = FlowRule(_id=flowrule.id, node_id=of_switch_id, _type='external', status='complete',
                                     priority=flowj.priority, internal_id=flow_id, table_id=0)
                Graph().addFlowRule(graph_id, flow_rule, None)
                                
            else:

                '''
                    It's a Endpoint-VNF flow
                '''

                VNFBridgeID = self.onosBusiness.getHostBridgeID(vnf_port.internal_id[0:11])
                ovsdbIPVNF  = self.onosBusiness.getBridgeOvsdbNodeIP(VNFBridgeID)

                '''
                #####################################################################################
                #       Check if the endpoint and the VNF are on the same compute node or not       #
                #####################################################################################
                '''

                if endpoint.node_id != ovsdbIPVNF and ONOS_ENABLED is True:
                    '''
                        The endpoint and the VNF are on different compute nodes
                    '''

                    # Create GRE tunnel
                    # Flow from endpoint to GRE endpoint
                    # Flow from GRE endpoint2 to VNF

                    gre_port = graph_id + "-gre-" + endpoint.node_id
                    endpoint1 = self.onosBusiness.getOvsdbIP(endpoint.node_id)
                    endpoint2 = ovsdbIPVNF
                                    
                    self.onosBusiness.createGreTunnel(endpoint1, INTEGRATION_BRIDGE, gre_port, endpoint1, endpoint2,
                                                      graph_id)
                    self.onosBusiness.createGreTunnel(endpoint2, INTEGRATION_BRIDGE, gre_port, endpoint2, endpoint1,
                                                      graph_id)

                    output_port = self.onosBusiness.getOfPort(endpoint1, INTEGRATION_BRIDGE, False, gre_port)
                    output_action = OnosAction()
                    output_action.setOutputAction(str(output_port))
                    actions.append(output_action)

                    '''
                    ###############################
                    #        Flow Creation        #
                    ###############################
                    '''

                    flowj = OnosFlow(priority=50000+flowrule.priority, of_switch_id=of_switch_id, actions=actions, match=match)
                    json_req = flowj.getJSON()

                    if DEBUG_MODE is True:
                        with open('onos_flow_Endpoint.txt', 'w') as outfile:
                            outfile.write(json_req)
                    flow_id = self.onosBusiness.createFlow(json_req)
                    
                    flow_rule = FlowRule(_id=flowrule.id, node_id=of_switch_id, _type='external', status='complete',priority=flowj.priority, internal_id=flow_id, table_id=0)  
                    Graph().addFlowRule(graph_id, flow_rule, None)

                    '''
                        SECOND ENDPOINT
                    '''

                    of_switch_id = self.onosBusiness.getBridgeID(endpoint2, INTEGRATION_BRIDGE)
                    input_port = self.ovsdb.getOfPort(endpoint2, INTEGRATION_BRIDGE, False, gre_port)

                    match.setInputMatch(str(input_port))

                    # [0:11] because internal_id will be like tapXXXXXXXX-XX
                    output_port = self.onosBusiness.getOfPort(endpoint2, INTEGRATION_BRIDGE, True, vnf_port.internal_id[0:11])
                    # Input port is returned as a number which identify the port within that bridge
                    vnf_port.of_port = str(output_port)

                    output_action = OnosAction()
                    output_action.setOutputAction(vnf_port.of_port)
                    actions.append(output_action)

                    flowj = OnosFlow(priority=50000+flowrule.priority, of_switch_id=of_switch_id, actions=actions, match=match)
                    json_req = flowj.getJSON()

                    if DEBUG_MODE is True:
                        with open('onos_flow_Endpoint.txt', 'w') as outfile:
                            outfile.write(json_req)
                    flow_id = self.onosBusiness.createFlow(json_req)
                    
                    flow_rule = FlowRule(_id=flowrule.id, node_id=of_switch_id, _type='external', status='complete',
                                         priority=flowj.priority, internal_id=flow_id, table_id=0)
                    Graph().addFlowRule(graph_id, flow_rule, None)

                else:
                    '''
                    #################################################
                    #       Endpoint and VNF on the same node       #
                    #################################################
                    '''               
                
                    actions = []

                    if vnf_port.of_port is None:
                
                        if ONOS_ENABLED is False:

                            output_port = self.ovsdb.getOfPort(ovs_id, INTEGRATION_BRIDGE, True, vnf_port.internal_id[0:8])
                            vnf_port.of_port = str(output_port)

                            output_action = Action()
                            output_action.setOutputAction(vnf_port.of_port, 65535)
                            actions.append(output_action)

                        else:

                            try:
                                output_port = self.onosBusiness.getOfPort(ovsdbIP, INTEGRATION_BRIDGE, True,
                                                                       vnf_port.internal_id[0:11])
                            except:
                                output_port = self.onosBusiness.getOfPort(INTEGRATION_BRIDGE_LOCAL_IP,
                                                                          INTEGRATION_BRIDGE, True, vnf_port.internal_id[0:11])

                            print("ENDPOINT TO VNF, VNF PORT: "+str(output_port))
                            # Input port is returned as a number which identify the port within that bridge
                            vnf_port.of_port = str(output_port)

                            output_action = OnosAction()
                            output_action.setOutputAction(vnf_port.of_port)
                            actions.append(output_action)

                    '''
                    ###############################
                    #        Flow Creation        #
                    ###############################
                    '''
                    if ONOS_ENABLED is False:

                        flow_id = str(profile_graph.id) + "_" + str(flowrule.id) 

                        flowj = Flow(flow_id, table_id=0, priority=16385+flowrule.priority, actions=actions, match=match)
                        json_req = flowj.getJSON()
                        #print (json_req)

                        ODL().createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, of_switch_id, flow_id, flowj.table_id)

                    else:

                        flowj = OnosFlow(priority=50000+flowrule.priority, of_switch_id=of_switch_id, actions=actions, match=match)
                        json_req = flowj.getJSON()

                        if DEBUG_MODE is True:
                            with open('onos_flow_Endpoint.txt', 'w') as outfile:
                                outfile.write(json_req)
                        flow_id = self.onosBusiness.createFlow(json_req)
                    
                    flow_rule = FlowRule(_id=flowrule.id, node_id=of_switch_id, _type='external', status='complete',priority=flowj.priority, internal_id=flow_id, table_id=0)  
                    Graph().addFlowRule(graph_id, flow_rule, None)

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
                                    
    def buildProfileGraph(self, nf_fg):
        profile_graph = ProfileGraph()
        profile_graph.setId(nf_fg.id)
        
        #Remove from the pool of available JOLnet networks vlans used in endpoints of type vlan
        for endpoint in nf_fg.end_points:
            if endpoint.type == 'vlan' and JOLNET_MODE is True:
                if endpoint.vlan_id.isdigit() is False:
                    name = endpoint.vlan_id
                else:                                
                    name = "exp" + str(endpoint.vlan_id)
                if name in JOLNET_NETWORKS:              
                    JOLNET_NETWORKS.remove(name)
        
        for vnf in nf_fg.vnfs:
            nf = self.buildVNF(vnf)
            profile_graph.addVNF(nf)
        
        for vnf in profile_graph.functions.values():
            self.setVNFNetwork(nf_fg, vnf, profile_graph)

        for endpoint in nf_fg.end_points:
            if endpoint.status is None:
                endpoint.status = "new"            
            profile_graph.addEndpoint(endpoint)
        
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
        return VNF(vnf.id, vnf, image, flavor, Configuration().AVAILABILITY_ZONE, status)
    
    def setVNFNetwork(self, nf_fg, nf, profile_graph):
        for port in nf.ports.values():
            if port.net is None and port.status != 'already_deployed':  
                for flowrule in nf_fg.getFlowRulesSendingTrafficFromPort(nf.id, port.id):
                    logging.debug(flowrule.getDict(True))
                    if flowrule.match is not None:
                        #check if vlan_id is constrained by an endpoint (only JOLNet)
                        if JOLNET_MODE is True:
                            for action in flowrule.actions:
                                if action.output is not None:
                                    if action.output.split(":")[0] == 'endpoint':
                                        endp = nf_fg.getEndPoint(action.output.split(":")[1])
                                        if endp.type =='vlan':
                                            net_vlan = endp.vlan_id
                                            if net_vlan.isdigit() is False:
                                                name = net_vlan
                                            else:                                
                                                name = "exp" + str(net_vlan)
                                            net_id = self.getNetworkIdfromName(name)
                                            port.net = net_id
                                            if name in JOLNET_NETWORKS:              
                                                JOLNET_NETWORKS.remove(name)                                                   
                                            break
                        #Choose a network arbitrarily (no constraints)    
                        if port.net is None:
                            name, net = self.getNetwork(port, profile_graph)
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
    
    def getOpenFlowSwitchID(self, ovs_id, bridge_name):
        '''
        Gets the OF_switch_id (e.g, openflow:64647512366924) of the bridge requested
        params:
            ovs_id:
                Openvswitch ID where the bridge is located
            bridge_name:
                Bridge for which we want to retrieve the OF_switchid
        '''        
        integration_bridge_dpid = self.ovsdb.getBridgeDPID(ovs_id, bridge_name)
        integration_bridge_dpid = integration_bridge_dpid.replace(":", "")
        of_switch_id = "openflow:" + str(int(integration_bridge_dpid,16))
        return of_switch_id    
    '''
    ######################################################################################################
    ###############################    Interactions with OpenStack       #################################
    ######################################################################################################
    '''
    def createServer(self, vnf, nf_fg):
        for port in vnf.listPort[:]:
            print(port.id)
            self.createPort(port, vnf, nf_fg) 
        json_data = vnf.getResourceJSON()
        resp = Nova().createServer(self.novaEndpoint, self.token.get_token(), json_data)
        vnf.OSid = resp['server']['id']
        
        #TODO: image location, location, type and availability_zone missing
        Graph().setVNFInternalID(nf_fg.db_id, vnf.id, vnf.OSid, 'complete')
    
    def deleteVNF(self, vnf, nf_fg, graph_id):
        Nova().deleteServer(self.novaEndpoint, self.token.get_token(), vnf.internal_id)
        #Graph().deleteFlowRuleFromVNF(vnf.db_id)
        #Graph().deleteVNFNetworks(graph_id, vnf.db_id)
        #Graph().deletePort(None, graph_id, vnf.db_id)
        for port in vnf.ports[:]:
            self.deletePort(port, graph_id)        
        Graph().deleteVNF(vnf.id, graph_id)
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
    
    def deletePort(self, port, graph_id):
        Neutron().deletePort(self.neutronEndpoint, self.token.get_token(), port.internal_id)
        #Graph().deleteFlowspecFromPort(port.id)
        #p = Graph().getPortFromInternalID(port.internal_id, graph_id)
        #Graph().deleteNetwork(p.os_network_id)
        Graph().deletePort(port.db_id, graph_id)
        # TODO: remove port from vnf

    def deleteUnusedNetworksAndSubnets(self):
        unused_networks_ref = Graph().getUnusedNetworks()
        for unused_network_ref in unused_networks_ref:
            subnet_id = Graph().getSubnet(unused_network_ref.id).id
            Neutron().deleteSubNet(self.neutronEndpoint, self.token.get_token(), subnet_id)
            Graph().deleteSubnet(unused_network_ref.id)
            Neutron().deleteNetwork(self.neutronEndpoint, self.token.get_token(), unused_network_ref.id)
            Graph().deleteNetwork(unused_network_ref.id)                    
                
    def addPortToVNF(self, port, vnf, nf_fg):
        vms = Graph().getVNFs(nf_fg.db_id)
        for vm in vms:
            if vm.graph_vnf_id == vnf.id:
                self.createPort(port, vnf, nf_fg)
                Nova().attachPort(self.novaEndpoint, self.token.get_token(), port.internal_id, vm.internal_id)
                break;
            
    def getNetwork(self, port, profile_graph):
        #if JOLNET_MODE is True:
            #return self.getUnusedNetwork()
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
        for network in JOLNET_NETWORKS[:]:
            network_free = True
            net_id = self.getNetworkIdfromName(network)
            if net_id is not None:
                #Check if there are ports on this network
                json_data = Neutron().getPorts(self.neutronEndpoint, self.token.get_token())
                ports = json.loads(json_data)['ports']
                for port in ports:
                    if port['network_id'] == net_id:
                        network_free = False
                        JOLNET_NETWORKS.remove(network)
                        break
                if network_free is False:
                    continue
                JOLNET_NETWORKS.remove(network)
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
