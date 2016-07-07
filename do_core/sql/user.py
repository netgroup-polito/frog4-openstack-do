'''
@author: AndreaVida
@author: stefanopetrangeli
'''

from sqlalchemy import Column, VARCHAR
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
import logging

from do_core.sql.sql_server import get_session
from do_core.exception import UserNotFound, TenantNotFound

Base = declarative_base()

class UserModel(Base):
    '''
    Maps the database table user
    '''
    __tablename__ = 'user'
    attributes = ['id', 'name', 'password', 'tenant_id', 'mail']
    id = Column(VARCHAR(64), primary_key=True)
    name = Column(VARCHAR(64))
    password = Column(VARCHAR(64))
    token = Column(VARCHAR(64))
    token_timestamp = Column(VARCHAR(64))
    tenant_id = Column(VARCHAR(64))
    mail = Column(VARCHAR(64))
    
class TenantModel(Base):
    '''
    Maps the database table tenant
    '''
    __tablename__ = 'tenant'
    attributes = ['id', 'name', 'description']
    id = Column(VARCHAR(64), primary_key=True)
    name = Column(VARCHAR(64))
    description = Column(VARCHAR(128))
    

class User(object):
    
    def __init__(self):
        pass
    
    def getUser(self, username):
        session = get_session()
        try:
            return session.query(UserModel).filter_by(name = username).one()
        except Exception as ex:
            logging.error(ex)
            raise UserNotFound("User not found: "+str(username)) from None
        
    def getUserByToken(self, token):
        session = get_session()
        try:
            return session.query(UserModel).filter_by(token = token).one()
        except Exception as ex:
            logging.error(ex)
            raise UserNotFound("Token not found: "+str(token)) from None        
    
    def getUserFromID(self, user_id):
        session = get_session()
        try:
            return session.query(UserModel).filter_by(id = user_id).one()
        except Exception as ex:
            logging.error(ex)
            raise UserNotFound("User not found id: "+str(user_id))
    
    def getTenantName(self, tenant_id):
        session = get_session()
        try:
            return session.query(TenantModel).filter_by(id = tenant_id).one().name
        except Exception as ex:
            logging.error(ex)
            raise TenantNotFound("User not found: "+str(tenant_id))
        
    def isUniqueToken(self, token):
        session = get_session()
        try:
            session.query(UserModel).filter_by(token = token).one()
            return False
        except Exception:
            return True
        
    def setNewToken(self, user_id, token, timestamp):
        session = get_session()
        with session.begin():
            session.query(UserModel).filter_by(id=user_id).update({"token":token,"token_timestamp":timestamp})
