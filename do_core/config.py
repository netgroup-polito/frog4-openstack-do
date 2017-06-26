'''
Created on Apr 18, 2016

@author: stefanopetrangeli
'''
import configparser, os, inspect
from do_core.exception import WrongConfigurationFile
    
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Configuration(object, metaclass=Singleton):
    
    def __init__(self):
        if os.getenv("FROG4_OPENSTACK_CONF") is not None:
            self.conf_file = os.environ["FROG4_OPENSTACK_CONF"]
        else:
            self.conf_file = "config/default-config.ini"

        self.inizialize()
    
    def inizialize(self): 
        config = configparser.RawConfigParser()
        base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])).rpartition('/')[0]
        try:
            if base_folder == "":
                config.read(base_folder + self.conf_file)
            else:
                config.read(base_folder + '/' + self.conf_file)
                
            self._ORCH_PORT = config.get('openstack_orchestrator','port')
            self._ORCH_IP = config.get('openstack_orchestrator','ip')
            self._ORCH_TIMEOUT = config.get('openstack_orchestrator','timeout')
            self._OPENSTACK_IP = config.get('openstack_orchestrator','openstack_ip')
            self._DEBUG_MODE = config.getboolean('openstack_orchestrator', 'debug_mode')
            self._IDENTITY_API_VERSION = config.getint('openstack_orchestrator','identity_api_version')
            self._AVAILABILITY_ZONE = config.get('openstack_orchestrator','availability_zone')

            self._TOKEN_EXPIRATION = config.get('authentication','token_expiration')
            
            self._JOLNET_MODE = config.getboolean('jolnet', 'jolnet_mode')

            if self._JOLNET_MODE is True:
                self._JOLNET_NETWORKS = [e.strip() for e in config.get('jolnet', 'jolnet_networks').split(',')]
            else:
                self._JOLNET_NETWORKS = None

            self._INTEGRATION_BRIDGE = config.get('topology','integration_bridge')
            self._EXIT_SWITCH = config.get('topology','exit_switch')

            if config.has_option('onos', 'address'):
                self._ONOS_ADDRESS  = config.get('onos','address')
                self._ONOS_USERNAME = config.get('onos','username')
                self._ONOS_PASSWORD = config.get('onos','password')
                self._ONOS_ENABLED  = config.get('onos','enabled')
                self._ONOS_INTEGRATION_BRIDGE_LOCAL_IP = config.get('onos', 'onos_integration_bridge_local_ip')

            if config.has_option('odl', 'address'):
                self._ODL_ADDRESS = config.get('odl','address')
                self._ODL_USERNAME = config.get('odl','username')
                self._ODL_PASSWORD = config.get('odl','password')
                self._INTEGRATION_BRIDGE_LOCAL_IP = config.get('odl', 'integration_bridge_local_ip')           
                
            self._LOG_FILE = config.get('log', 'log_file')
            self._VERBOSE = config.getboolean('log', 'verbose')
            self._DEBUG = config.getboolean('log', 'debug')
            
            self._CONNECTION = config.get('db','connection')
            
            self._DOMAIN_DESCRIPTION_TOPIC = config.get('domain_description','topic')
            self._DOMAIN_DESCRIPTION_FILE = config.get('domain_description','file')
                        
            self._DD_NAME = config.get('doubledecker','dd_name')
            self._DD_CUSTOMER = config.get('doubledecker','dd_customer')
            self._BROKER_ADDRESS = config.get('doubledecker','broker_address')
            self._DD_KEYFILE = config.get('doubledecker','dd_keyfile')

            self._TEMPLATE_SOURCE = config.get('templates','source')
            if config.has_option('templates', 'path'):
                self._TEMPLATE_PATH = config.get('templates','path')
            else:
                self._TEMPLATE_PATH = None
            if config.has_option('templates', 'repository_url'):
                self._TEMPLATE_REPOSITORY_URL = config.get('templates', 'repository_url')
            else:
                self._TEMPLATE_REPOSITORY_URL = None
                
        except Exception as ex:
            raise WrongConfigurationFile(str(ex))
    
    @property
    def ORCH_TIMEOUT(self):
        return self._ORCH_TIMEOUT
    
    @property
    def IDENTITY_API_VERSION(self):
        return self._IDENTITY_API_VERSION
        
    @property
    def TOKEN_EXPIRATION(self):
        return self._TOKEN_EXPIRATION
    
    @property
    def JOLNET_NETWORKS(self):
        return self._JOLNET_NETWORKS
    
    @property
    def DOMAIN_DESCRIPTION_TOPIC(self):
        return self._DOMAIN_DESCRIPTION_TOPIC
    
    @property
    def DOMAIN_DESCRIPTION_FILE(self):
        return self._DOMAIN_DESCRIPTION_FILE   

    @property
    def DD_NAME(self):
        return self._DD_NAME
    
    @property
    def DD_CUSTOMER(self):
        return self._DD_CUSTOMER    
    
    @property
    def BROKER_ADDRESS(self):
        return self._BROKER_ADDRESS
    
    @property
    def DD_KEYFILE(self):
        return self._DD_KEYFILE    
    
    @property
    def DEBUG_MODE(self):
        return self._DEBUG_MODE

    @property
    def JOLNET_MODE(self):
        return self._JOLNET_MODE

    @property
    def TEMPLATE_SOURCE(self):
        return self._TEMPLATE_SOURCE
    
    @property
    def TEMPLATE_PATH(self):
        return self._TEMPLATE_PATH
    
    @property
    def TEMPLATE_REPOSITORY_URL(self):
        return self._TEMPLATE_REPOSITORY_URL

    @property
    def ORCH_IP(self):
        return self._ORCH_IP
    
    @property
    def OPENSTACK_IP(self):
        return self._OPENSTACK_IP
    
    @property
    def ORCH_PORT(self):
        return self._ORCH_PORT
        
    @property
    def CONNECTION(self):
        return self._CONNECTION

    @property
    def LOG_FILE(self):
        return self._LOG_FILE

    @property
    def VERBOSE(self):
        return self._VERBOSE

    @property
    def DEBUG(self):
        return self._DEBUG
    
    @property
    def EXIT_SWITCH(self):
        return self._EXIT_SWITCH
    
    @property
    def INGRESS_SWITCH(self):
        return self._INGRESS_SWITCH
    
    @property
    def INTEGRATION_BRIDGE(self):
        return self._INTEGRATION_BRIDGE
    
    @property
    def ONOS_ADDRESS(self):
        return self._ONOS_ADDRESS
    
    @property
    def ONOS_USERNAME(self):
        return self._ONOS_USERNAME
    
    @property
    def ONOS_PASSWORD(self):
        return self._ONOS_PASSWORD

    @property
    def ONOS_ENABLED(self):
        return self._ONOS_ENABLED
    
    @property
    def AVAILABILITY_ZONE(self):
        return self._AVAILABILITY_ZONE

    @property
    def INTEGRATION_BRIDGE_LOCAL_IP(self):
        return self._INTEGRATION_BRIDGE_LOCAL_IP

    @property
    def ONOS_INTEGRATION_BRIDGE_LOCAL_IP(self):
        return self._ONOS_INTEGRATION_BRIDGE_LOCAL_IP
    
