'''
Created on 15 apr 2016

@author: stefanopetrangeli
'''
from .sql.user import User
from do_core.exception import unauthorizedRequest, UserTokenExpired
from do_core.config import Configuration

import hashlib, time, uuid, logging

class UserData(object):
    
    def __init__(self, username=None, password=None, tenant=None, token=None):
        self.username = username
        self.password = password
        self.tenant = tenant
        self.token = token
    
    def getUserID(self):
        return User().getUser(self.username).id
    
    def getUserData(self, user_id):
        user = User().getUserFromID(user_id)
        self.username = user.name
        self.password = user.password
        self.token = user.token
        tenant = User().getTenantName(user.tenant_id)
        self.tenant = tenant

class UserAuthentication(object):
    
    token_expiration = int(Configuration().TOKEN_EXPIRATION)
    
    def authenticateUserFromRESTRequest(self, request):
        token = request.get_header("X-Auth-Token")  
        if token is None:
            raise unauthorizedRequest('Token required')
        return self.authenticateUserFromToken(token)
    
    """
    def getPasswordHash(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    """   
    
    def isAnExpiredToken(self, token_timestamp):
        if token_timestamp is None:
            return True
        token_timestamp = int(token_timestamp)
        tt = int(time.time())
        return ( ( tt - token_timestamp) > self.token_expiration )
        
    
    def authenticateUserFromCredentials(self, credentials):
        if "username" in credentials and "password" in credentials:
            username = credentials["username"]
            password = credentials["password"]
        else:
            raise unauthorizedRequest('Authentication credentials required')

        user = User().getUser(username)
        #passwordhash_check = self.getPasswordHash(password)
        if user.password == password:
            if user.token is not None and self.isAnExpiredToken(user.token_timestamp) is False:
                logging.debug("User successfully authenticated")
                return user.token
            else:
                # generate token and return 
                token, token_timestamp = self.generateToken()
                User().setNewToken(user.id, token, token_timestamp)
                return token
        else:
            logging.debug("Wrong password")
            raise unauthorizedRequest('Login failed')
        
    def authenticateUserFromToken(self, token):
        user = User().getUserByToken(token)
        if self.isAnExpiredToken(user.token_timestamp) is True:
            logging.debug("Token expired")
            raise UserTokenExpired("Token expired. You must authenticate again with user/pass")
        else:
            tenantName = User().getTenantName(user.tenant_id)
            userobj = UserData(user.name, user.password, tenantName, token)
            return userobj

    def generateToken(self):
        unique = False
        while not unique:
            token = uuid.uuid4().hex
            timestamp = time.time()
            unique = User().isUniqueToken(token)
        
        timestamp = int(timestamp)
        return token, timestamp