'''
Created on 23 giu 2016

@author: stefanopetrangeli
'''
import json, logging

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class ResourceDescription(object, metaclass=Singleton):
    def __init__(self, file):
        self.file = file
        self.dict = None
        self.parse()
        self.endpoints = self.dict["frog-domain:informations"]["frog-network-manager:informations"]["openconfig-interfaces:interfaces"]["openconfig-interfaces:interface"]
                
    def parse(self):
        try:
            description_file = open(self.file,"r")
            self.dict = json.loads(description_file.read())
        except ValueError as ex:
            logging.error("Resource description file is not a valid json")
            raise ex
    
    def getEndpointDesc(self, endpoint):
        for endp in self.endpoints:
            if '/' in endp['name']:
                tmp = endp['name'].split("/")
                node_id = tmp[0]
                if_name = tmp[1]
                if node_id == endpoint.node_id and if_name == endpoint.interface:
                    return endp
            else:
                if endp['name'] == endpoint.interface:
                    return endp
        return None
        
    def addEndpoint(self, endpoint):
        if endpoint.type == "vlan":
            endpoint_desc = self.getEndpointDesc(endpoint)
            vlan = int(endpoint.vlan_id)
            if endpoint_desc is not None and self.supportsVlan(endpoint_desc):
                vlan_list = self.getFreeVlans(endpoint_desc)
                if vlan in vlan_list:
                    # Remove from free vlans the vlan_id of the new endpoint
                    vlan_list.remove(vlan)
                    self.setFreeVlans(endpoint_desc, vlan_list)

    def deleteEndpoint(self, endpoint):
        if endpoint.type == "vlan":
            endpoint_desc = self.getEndpointDesc(endpoint)
            vlan = int(endpoint.vlan_id)
            if endpoint_desc is not None and self.supportsVlan(endpoint_desc):
                vlan_list = self.getFreeVlans(endpoint_desc)
                if vlan not in vlan_list:
                    # Add to free vlans the vlan_id of the endpoint removed
                    vlan_list.append(vlan)
                    self.setFreeVlans(endpoint_desc, vlan_list)                    
                
                
    def supportsVlan(self, endpoint_desc):
        if 'openconfig-if-ethernet:ethernet' in endpoint_desc:
            if 'openconfig-vlan:vlan' in endpoint_desc['openconfig-if-ethernet:ethernet']:
                if 'openconfig-vlan:config' in endpoint_desc['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan']:
                    vlan_config = endpoint_desc['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan']['openconfig-vlan:config']
                    if vlan_config['interface-mode'] == "TRUNK":
                        return True
        return False
    
    def getFreeVlans(self, endpoint_desc):
        vlan_list = []
        vlan_config = endpoint_desc['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan']['openconfig-vlan:config']
        for vlan in vlan_config['trunk-vlans']:
            if type(vlan) is str and ".." in vlan:
                tmp = vlan.split("..")
                lower_vlan = int(tmp[0])
                upper_vlan = int(tmp[1])
                vlan_list += list(range(lower_vlan, upper_vlan + 1))
            else:
                vlan_list += [vlan]
        return vlan_list
    
    def setFreeVlans(self, endpoint_desc, vlan_list):
        vlan_output_list = []
        vlan_list.sort()
        vlan_ranges = list(self.ranges(vlan_list))
        for vlan_range in vlan_ranges:
            if vlan_range[0] == vlan_range[1]:
                vlan_output_list.append(vlan_range[0])
            else:
                vlan_output_list.append(str(vlan_range[0]) + ".." + str(vlan_range[1]))
        vlan_config = endpoint_desc['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan']['openconfig-vlan:config']
        vlan_config['trunk-vlans'] = vlan_output_list

    def ranges(self,seq):
        '''
        Given a sequence it returns ranges of consecutive numbers
        '''
        start, end = seq[0], seq[0]
        count = start
        for item in seq:
            if not count == item:
                yield start, end
                start, end = item, item
                count = item
            end = item
            count += 1
        yield start, end
        
    def writeToFile(self):
        description_file = open(self.file,"w")
        description_file.write(json.dumps(self.dict, indent=2, separators=(',', ': ')))
