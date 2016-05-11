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

IDENTITY_VERSION_CONF = Configuration().IDENTITY_VERSION

#ADMIN_TENANT_NAME = Configuration().ADMIN_TENANT_NAME
#ADMIN_USER = Configuration().ADMIN_USER
#ADMIN_PASSWORD = Configuration().ADMIN_PASSWORD

class KeystoneAuthentication(object):
    '''
    Class used to store the user keystone information and executes the REST call to OpenStack API
    Each instance is referred to an user that pass on the constructor the keyston_server URL, the tenant name and the access credentials
    The method createToken() asks the access token to the keystone server it is called by the constructor and successively it should be called when the token expires
    '''

    def __init__(self, keystone_server, username = None, password = None, tenant_name = None, domain="default", user_token = None, orch_token = None):
#    def __init__(self, keystone_server, tenant_name, username, password):
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
        if IDENTITY_VERSION_CONF.isdigit() is False:
            #TODO: autodetect
            pass
        else:
            if int(IDENTITY_VERSION_CONF) == 2:
                self.identity_version = 2
                self.keystone_authentication_url = self.keystone_server+"/v2.0/tokens"
                self.authenticationData = {'auth':{'tenantName': tenant_name, 'passwordCredentials':{'username': username, 'password': password}}}
            elif int(IDENTITY_VERSION_CONF) == 3:
                self.identity_version = 3
                self.keystone_authentication_url = self.keystone_server+"/v3/auth/tokens"
                self.authenticationData = {"auth":{"identity":{"methods":["password"],"password":{"user":{"domain":{"name": domain},"password":password,"name":username}}},"scope":{"project":{"domain":{"name":domain},"name":tenant_name}}}}
        # if admin_token is None --> Orchestrator instance
        if orch_token is None and tenant_name is not None and username is not None and password is not None:
            #logging.debug(json.dumps(self.authenticationData))
            self.ServiceCreateToken()
        # else -> User keystone_auth instance
        """
        elif orch_token is not None and user_token is not None:
            self.token = user_token
            self.orchToken= orch_token
            self.retrieveUserData(user_token)
        """
    
            
    def retrieveUserData(self, rawToken):
        '''
        @author: Alex Palesandro
        
        Validates a user token
        The token received as input is the complete token (NOT the MD5 version)
        Exceptions:
            raise an HTTPunauthorized if the token is wrong or no longer valid
        '''
        if (self.validateToken(self.keystone_server, rawToken, self.orchToken)):
                return self.get_info_by_Token(rawToken, self.orchToken)
        else:
                raise falcon.HTTPUnauthorized("HTTPUnauthorized",
                                              "Token not valid")
                
    def get_info_by_Token_id(self, token, admin_token):
        '''
        @author: Fabio Mignini
        
        Retrieve information about token and store them in self.tokendata
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or unauthorized credentials
        '''   
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': admin_token}
        resp = requests.get(self.keystone_server+"/v2.0/tokens/"+token, headers=headers)
        resp.raise_for_status()
        self.tokendata = json.loads(resp.text)
    
    def get_info_by_Token(self, token, admin_token):
        '''
        @author: Fabio Mignini
        
        Retrieve information about token and store them in self.tokendata
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or unauthorized credentials
        '''   
        
        md5Token = self.getTokenID(token)
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': admin_token}
        resp = requests.get(self.keystone_server+"/v2.0/tokens/"+md5Token, headers=headers)
        resp.raise_for_status()
        self.tokendata = json.loads(resp.text)
        #print(json.dumps(self.tokendata))
        
    def validateToken(self,keystone_server, Token, admin_token):
        '''
        @author: Fabio Mignini
        
        Validate the token passed in the function
        Return true if the token is valid, false if it is not valid
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or unauthorized credentials
        '''   
        #m = hashlib.md5()
        #m.update(Token)
        #md5Token = m.digest();
        
        md5Token = self.getTokenID(Token)
        
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': admin_token}
        resp = requests.head(keystone_server+"/v2.0/tokens/"+md5Token, headers=headers)
        #if status code is 404 the token passed is not valid,
        #if status code is 401 the orchestrator_core token is not valid.
        logging.debug(resp.status_code)
        if resp.status_code == 204 or resp.status_code == 200:
            #print "User Authenticated - PUT"
            return True
        return False
    
    """
    def validateToken(self, admin_token):
        '''
        @author: Fabio Mignini
        
        Validate the token stored in the class
        Return true if the token is valid, false if it is not valid
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or unauthorized credentials
        '''   
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': admin_token}
        resp = requests.head(self.keystone_server+"/v2.0/tokens/"+self.get_token(), headers=headers)
        if resp.status_code == 204:
            return True
        return False
    """
    @staticmethod
    def createUserToken(keystone_server,username,tenant_name,password):
        '''
        Require the token to keystone server
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or unauthorized credentials
        '''
        keystone_authentication_url = keystone_server+"/v2.0/tokens"
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        authenticationData = {'auth':{'tenantName': tenant_name, 'passwordCredentials':{'username': username, 'password': password}}}
        resp = requests.post(keystone_authentication_url, data=json.dumps(authenticationData), headers=headers)
        resp.raise_for_status()
        tokendata = json.loads(resp.text)
        return tokendata
        #self.token = self.tokendata['access']['token']['id']
        
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
        if self.identity_version == 3:
            self.token = resp.headers['X-Subject-Token']
        
    def getTokenID(self, Token):
        hasher = hashlib.new('md5')
        if not isinstance(Token, six.text_type):
            token_id = Token.encode('utf-8')
        else:
            token_id = Token.encode('utf-8')
        hasher.update(token_id)
        md5Token = hasher.hexdigest()
        return md5Token
        
    def get_tenantID(self): 
        '''
        Return the tenant ID of the user
        '''
        return self.tokendata['access']['token']['tenant']['id']
    
    def get_userID_by_token(self, token, admin_token):
        '''
        @author: Fabio Mignini
        
        Return the user of the token passed
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error or unauthorized credentials
        '''   
        md5Token = self.getTokenID(token)
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Auth-Token': admin_token}
        resp = requests.get(self.keystone_server+"/v2.0/tokens/"+md5Token, headers=headers)
        resp.raise_for_status()
        tokendata = json.loads(resp.text)
        return tokendata['access']['user']['id']
            
    def get_userID(self):
        '''
        @author: Fabio Mignini
        
        Return the user ID of the user
        '''
        return self.tokendata['access']['user']['id']
    
    def get_username(self):
        '''
        @author: Fabio Mignini
        
        Return the user ID of the user
        '''
        return self.tokendata['access']['user']['name']
    
    def get_token(self):
        '''
        Return the access token to authenticate to the OpenStack services
        '''
        #return self.tokendata['access']['token']['id']
        return self.token
    
    def get_endpoints(self, service):
        '''
        Return the list of the endpoints of a service
        Args:
            service:
                String that specifies the type of service of the searched endpoints
        '''
        if self.identity_version == 2:
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
        if self.identity_version == 2:
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
        if self.identity_version == 2:
            if self.tokendata['access']['token']['id'] is None:              
                raise falcon.HTTPUnauthorized("HTTPUnauthorized", "Token not valid")
            else:
                self.token = self.tokendata['access'][ 'token']['id']

    def checkMyToken(self):
        '''
        Return the list of the endpoints of a service
        Args:
            service:
                String that specifies the type of service of the searched endpoints
        '''
        if self.validateToken(self.keystone_server, self.orchToken, self.orchToken) is not True:
            try:
                self.keystone_authentication_url.ServiceCreateToken();
            except:
                raise falcon.HTTPUnauthorized("HTTPUnauthorized", "Token not valid")

    def get_admin_token(self):
        '''
        @author: Alex Palesandro
        
        Return the user ID of the user
        '''
        return self.orchToken
