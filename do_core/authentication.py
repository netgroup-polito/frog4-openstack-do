'''
Created on Oct 1, 2014

@author: fabiomignini
@author: stefanopetrangeli
'''

import requests
import json
import falcon
import hashlib
import logging
import six
from do_core.config import Configuration
from do_core.exception import WrongConfigurationFile

IDENTITY_API_VERSION = Configuration().IDENTITY_API_VERSION

class KeystoneAuthentication(object):
    '''
    Class used to store the user keystone information and executes the REST call to OpenStack API
    Each instance is referred to an user that pass on the constructor the keyston_server URL, the tenant name and the access credentials
    The method createToken() asks the access token to the keystone server it is called by the constructor and successively it should be called when the token expires
    '''

    def __init__(self, keystone_server, username = None, password = None, tenant_name = None, domain="default"):
        '''
        Constructor
        Args:
            keystone_server:
                URL of the keyston server (example http://serverAddr:keystonePort/v2.0/tokens)
            tenant_name:
                name of the user tenant
            username:
                username to authenticate
            password:
                secret of the user that requires the authentication
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or unauthorized credentials
        '''
        self.keystone_server = keystone_server
        if IDENTITY_API_VERSION == 2:
            self.keystone_authentication_url = self.keystone_server+"/v2.0/tokens"
            self.authenticationData = {'auth':{'tenantName': tenant_name, 'passwordCredentials':{'username': username, 'password': password}}}
        elif IDENTITY_API_VERSION == 3:
            self.keystone_authentication_url = self.keystone_server+"/v3/auth/tokens"
            self.authenticationData = {"auth":{"identity":{"methods":["password"],"password":{"user":{"domain":{"name": domain},"password":password,"name":username}}},"scope":{"project":{"domain":{"name":domain},"name":tenant_name}}}}
        else:
            raise WrongConfigurationFile("Identity_api_version should be 2 or 3")
        
        #logging.debug(json.dumps(self.authenticationData))
        self.ServiceCreateToken()
    
        
    def createToken(self):
        '''
        Require the token to keystone server
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or unauthorized credentials
        '''
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        resp = requests.post(self.keystone_authentication_url, data=json.dumps(self.authenticationData), headers=headers)
        resp.raise_for_status()
        self.tokendata = json.loads(resp.text)
        if IDENTITY_API_VERSION == 3:
            self.token = resp.headers['X-Subject-Token']
    
    def get_endpoints(self, service):
        '''
        Return the list of the endpoints of a service
        Args:
            service:
                String that specifies the type of service of the searched endpoints
        '''
        if IDENTITY_API_VERSION == 2:
            for x in self.tokendata['access']['serviceCatalog']:
                if x['type'] == service:
                    return x['endpoints']
            return []
        else:
            for x in self.tokendata['token']['catalog']:
                if x['type'] == service:
                    return x['endpoints']
            return []
        
    def get_endpoint_URL(self, service, _type):
        '''
        Return the endpoint URL of the specified service and type
        Args:
            service:
                String that specifies the type of service of the searched endpoints
            type:
                String that specifies the type of the URL (public, internal, admin) requested
        '''
        if IDENTITY_API_VERSION == 2:
            for x in self.tokendata['access']['serviceCatalog']:
                if x['type'] == service:
                    for endpoint in x['endpoints']:
                        if _type + 'URL' in endpoint:
                            return endpoint[_type + 'URL']
            return None
        else:
            for x in self.tokendata['token']['catalog']:
                if x['type'] == service:
                    for endpoint in x['endpoints']:
                        if endpoint['interface'] == _type:
                            return endpoint['url']
            return None      
    
    def ServiceCreateToken(self):
        '''
        @author: Alex Palesandro
        
        Wraps the create token raising an exception if the token is not valid for some reason
        '''
        self.createToken()
        if IDENTITY_API_VERSION == 2:
            if self.tokendata['access']['token']['id'] is None:              
                raise falcon.HTTPUnauthorized("HTTPUnauthorized", "Token not valid")
            else:
                self.token = self.tokendata['access'][ 'token']['id']

    def get_token(self):
        '''
        Return the access token to authenticate to the OpenStack services
        '''
        if IDENTITY_API_VERSION == 2:
            return self.tokendata['access']['token']['id']
        return self.token
