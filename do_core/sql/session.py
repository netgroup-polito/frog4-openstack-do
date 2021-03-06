'''
@author: fabiomignini
@author: stefanopetrangeli
'''
from sqlalchemy import Column, DateTime, func, VARCHAR, Text, not_, desc
from do_core.sql.sql_server import get_session
from sqlalchemy.ext.declarative import declarative_base
from do_core.exception import sessionNotFound
import datetime
import logging

Base = declarative_base()

class SessionModel(Base):
    '''
    Maps the database table session
    '''
    __tablename__ = 'session'
    attributes = ['id', 'user_id', 'service_graph_id', 'service_graph_name', 'status','started_at',
                  'last_update','error','ended']
    id = Column(VARCHAR(64), primary_key=True)
    user_id = Column(VARCHAR(64))
    service_graph_id = Column(Text)
    service_graph_name = Column(Text)
    status = Column(Text)
    started_at = Column(Text)
    last_update = Column(DateTime, default=func.now())
    error = Column(Text)
    ended = Column(DateTime)

class Session(object):
    def __init__(self):
        pass
    
    def inizializeSession(self, session_id, user_id, service_graph_id, service_graph_name):
        '''
        inizialize the session in db
        '''
        session = get_session()  
        with session.begin():
            session_ref = SessionModel(id=session_id, user_id = user_id, service_graph_id = service_graph_id, 
                                started_at = datetime.datetime.now(), service_graph_name=service_graph_name,
                                last_update = datetime.datetime.now(), status='inizialization')
            session.add(session_ref)
        pass

    def updateStatus(self, session_id, status):
        session = get_session()  
        with session.begin():
            session.query(SessionModel).filter_by(id = session_id).filter_by(ended = None).filter_by(error = None).update({"last_update":datetime.datetime.now(), 'status':status})

    def updateUserID(self, session_id, user_id):
        session = get_session()  
        with session.begin():
            session.query(SessionModel).filter_by(id = session_id).filter_by(ended = None).filter_by(error = None).update({"user_id":user_id})

    def get_active_user_session(self, user_id):
        '''
        returns if exists an active session of the user
        '''
        session = get_session()
        session_ref = session.query(SessionModel).filter_by(user_id = user_id).filter_by(ended = None).filter_by(error = None).first()
        if session_ref is None:
            raise sessionNotFound("Session Not Found")
        return session_ref
    
    def set_ended(self, session_id):
        '''
        Set the ended status for the session identified with session_id
        '''
        session = get_session() 
        with session.begin():       
            session.query(SessionModel).filter_by(id=session_id).update({"ended":datetime.datetime.now()}, synchronize_session = False)

    def set_error(self, session_id):
        '''
        Set the error status for the active session associated to the user id passed
        '''
        session = get_session()
        with session.begin():
            logging.debug("Put session for session "+str(session_id)+" in error")
            session.query(SessionModel).filter_by(id=session_id).filter_by(ended = None).filter_by(error = None).update({"error":datetime.datetime.now()}, synchronize_session = False)

    def get_active_user_session_by_nf_fg_id(self, service_graph_id, error_aware=True):
        session = get_session()
        if error_aware:
            session_ref = session.query(SessionModel).filter_by(service_graph_id = service_graph_id).filter_by(ended = None).filter_by(error = None).first()
        else:
            session_ref = session.query(SessionModel).filter_by(service_graph_id = service_graph_id).filter_by(ended = None).order_by(desc(SessionModel.started_at)).first()
        if session_ref is None:
            raise sessionNotFound("Session Not Found, for servce graph id: "+str(service_graph_id))
        return session_ref

    def get_service_graph_info(self,session_id):
        session = get_session()
        return session.query(SessionModel.service_graph_id, SessionModel.service_graph_name).filter_by(id = session_id).one()

    def check_nffg_id(self, nffg_id):
        session = get_session()
        with session.begin():
            return session.query(SessionModel).filter_by(service_graph_id = nffg_id).all()

    def get_nffg_id(self, session_id):
        session = get_session()
        return session.query(SessionModel).filter_by(id = session_id).one()


    def getAllNFFG(self):
        session = get_session()
        return session.query(SessionModel).all()
