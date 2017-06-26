'''
@author: fabiomignini
@author: stefanopetrangeli
'''
import logging, json, requests, uuid, os, inspect
from vnf_template_library.template import Template
from vnf_template_library.validator import ValidateTemplate
from do_core.config import Configuration
from nffg_library.validator import ValidateNF_FG
from do_core.exception import VNFRepositoryError, WrongConfigurationFile
from nffg_library.nffg import NF_FG

TEMPLATE_SOURCE = Configuration().TEMPLATE_SOURCE
TEMPLATE_REPOSITORY_URL = Configuration().TEMPLATE_REPOSITORY_URL
TEMPLATE_PATH = Configuration().TEMPLATE_PATH

class NFFG_Manager(object):
    
    def __init__(self, nffg):
        self.nffg = nffg
        self.stored_templates = {}
    # Templates
        
    def addTemplates(self):
        '''
        Retrieve the Templates of all the VNFs in the graph
        '''
        for vnf in self.nffg.vnfs[:]:
            self.addTemplate(vnf, vnf.vnf_template_location)
   
    def addTemplate(self, vnf,  uri):
        '''
        Retrieve the Template of a specific VNF.
        It is possible that the template of a VNF is a graph,
        in that case that VNF will be expanded.
        The two graph will be connected together,
        accordingly to the original connection of the VNF that has been expanded.
        '''
        logging.debug("Getting manifest: "+str(uri)+" of vnf: "+str(vnf.name))
        template = self.getTemplate(uri)
        
        if template.checkExpansion() is True:
            logging.debug("Expanding a VNF: "+str(vnf.name))
            nffg_from_template = self.getNFFGDict(template.uri)
            # Validate forwarding graph
            ValidateNF_FG().validate(nffg_from_template)
            
            internal_nffg = NF_FG()
            internal_nffg.parseDict(nffg_from_template)
            NFFG_Manager(internal_nffg).addTemplates()
            
            self.nffg.expandNode(vnf, internal_nffg)
        
        else:    
            vnf.addTemplate(template)
            # Check min port and max port
            vnf.checkPortsAgainstTemplate() 
    
    def getTemplate(self, uri):
        template_dict = self.getTemplateDict(uri)
        ValidateTemplate().validate(template_dict)
        template = Template()
        template.parseDict(template_dict)
        return template
    
    def getNFFGDict(self, filename): 
        base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])).rpartition('/')[0]
        return self.getDictFromFile(base_folder+"/graphs/", filename)
    
    def getTemplateDict(self, uri):  
        if TEMPLATE_SOURCE == "datastore":
            if uri in self.stored_templates:
                return self.stored_templates[uri]
            return self.getDictFromVNFRepository(uri)
        #elif TEMPLATE_SOURCE == "glance":
        #    return self.getDictFromGlance(uri)
        elif TEMPLATE_SOURCE == "file":
            base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])).rpartition('/')[0]
            return self.getDictFromFile(base_folder+'/'+TEMPLATE_PATH, uri)
        else:
            raise WrongConfigurationFile("source configuration inside the templates section has a value not allowed")
        
    def getDictFromFile(self, path, filename):
        json_data=open(path+filename).read()
        return json.loads(json_data)
    """
    def getDictFromGlance(self, uri):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': self.token}
        resp = requests.get(uri, headers=headers)
        resp.raise_for_status()
        return json.loads(resp.text)
    """
    def getDictFromVNFRepository(self, uri):
        try:
            actual_uri = uri
            if uri.endswith(".json"):
                actual_uri = uri[:-len(".json")]
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
            resp = requests.get(TEMPLATE_REPOSITORY_URL + actual_uri, headers=headers)
            resp.raise_for_status()
            template_dict = resp.json()
            self.stored_templates[uri] = template_dict
            return template_dict
        except Exception as ex:
            raise VNFRepositoryError("An error occurred while contacting the VNF Repository")
        
