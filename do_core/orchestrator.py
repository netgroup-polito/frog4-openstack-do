'''
Created on Apr 15, 2016

@author: stefanopetrangeli
'''

import falcon
import logging
import requests
import json

from sqlalchemy.orm.exc import NoResultFound
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG

from do_core.controller import OpenstackOrchestratorController
from do_core.userAuthentication import UserAuthentication
from do_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, ingoingFlowruleMissing, ManifestValidationError, UserNotFound, UserTokenExpired
#from do_core.nffg_manager import NFFG_Manager

class NFFGStatus(object):
    def on_get(self, request, response, nffg_id):
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
                   
            controller = OpenstackOrchestratorController(user_data)
            response.body = controller.getStatus(nffg_id)
            
            response.status = falcon.HTTP_200
            
        except NoResultFound:
            logging.exception("EXCEPTION - NoResultFound")
            raise falcon.HTTPNotFound()
        except requests.HTTPError as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError(str(err), err.response.text)
        except sessionNotFound as err:
            logging.exception(err.message)
            raise falcon.HTTPNotFound()
        except ingoingFlowruleMissing as err:
            logging.exception(err.message)
            raise falcon.HTTPInternalServerError('ingoingFlowruleMissing',err.message)
        except ManifestValidationError as err:
            logging.exception(err.message)
            raise falcon.HTTPInternalServerError('ManifestValidationError',err.message)
        except (unauthorizedRequest, UserNotFound) as err:
            if request.get_header("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.get_header("X-Auth-User"))
            logging.debug(err.message)                
            raise falcon.HTTPUnauthorized("Unauthorized", err.message)
        except Exception as ex:
            logging.exception(ex)
            raise falcon.HTTPInternalServerError('Contact the admin. ',str(ex))
      
class OpenstackOrchestrator(object):
    '''
    Admin class that intercept the REST call through the WSGI server
    '''
    def on_delete(self, request, response, nffg_id):
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
                   
            controller = OpenstackOrchestratorController(user_data)
            response.body = controller.delete(nffg_id)
            
        except NoResultFound:
            logging.exception("EXCEPTION - NoResultFound")
            raise falcon.HTTPNotFound()
        except requests.HTTPError as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError(str(err), err.response.text)
        except sessionNotFound as err:
            logging.exception(err.message)
            raise falcon.HTTPNotFound()
        except ingoingFlowruleMissing as err:
            logging.exception(err.message)
            raise falcon.HTTPInternalServerError('ingoingFlowruleMissing',err.message)
        except ManifestValidationError as err:
            logging.exception(err.message)
            raise falcon.HTTPInternalServerError('ManifestValidationError',err.message)
        except UserTokenExpired as err:
            logging.debug("User token is expired")
            raise falcon.HTTPUnauthorized("User token expired", err.message)        
        except (unauthorizedRequest, UserNotFound) as err:
            if request.get_header("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.get_header("X-Auth-User"))
            logging.debug(err.message)                
            raise falcon.HTTPUnauthorized("Unauthorized", err.message)
        except Exception as ex:
            logging.exception(ex)
            raise falcon.HTTPInternalServerError('Contact the admin. ',str(ex))
    
    def on_get(self, request, response, nffg_id):
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
                   
            controller = OpenstackOrchestratorController(user_data)
            response.body = controller.get(nffg_id)
            
            response.status = falcon.HTTP_200
            
        except NoResultFound:
            logging.exception("EXCEPTION - NoResultFound")
            raise falcon.HTTPNotFound()
        except requests.HTTPError as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError(str(err), err.response.text)
        except requests.ConnectionError as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError(str(err), "Connection error")        
        except sessionNotFound as err:
            logging.exception(err.message)
            raise falcon.HTTPNotFound()
        except ingoingFlowruleMissing as err:
            logging.exception(err.message)
            raise falcon.HTTPInternalServerError('ingoingFlowruleMissing',err.message)
        except ManifestValidationError as err:
            logging.exception(err.message)
            raise falcon.HTTPInternalServerError('ManifestValidationError',err.message)
        except UserTokenExpired as err:
            logging.debug("User token is expired")
            raise falcon.HTTPUnauthorized("User token expired", err.message)        
        except (unauthorizedRequest, UserNotFound) as err:
            if request.get_header("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.get_header("X-Auth-User"))
            logging.debug(err.message)
            raise falcon.HTTPUnauthorized("Unauthorized", err.message)
        except Exception as ex:
            logging.exception(ex)
            raise falcon.HTTPInternalServerError('Contact the admin. ',str(ex))
        
    def on_put(self, request, response, nffg_id = None):
        """
        Take as body request the NF-FG      
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
            
            nffg_dict = json.loads(request.stream.read().decode())
            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)
            
            controller = OpenstackOrchestratorController(user_data)
            response.body = controller.put(nffg)
            response.content_type = "text/plain"
            response.status = falcon.HTTP_202
            
        except wrongRequest as err:
            logging.exception(err)
            raise falcon.HTTPBadRequest("Bad Request", err.description)
        except UserTokenExpired as err:
            logging.debug("User token is expired")
            raise falcon.HTTPUnauthorized("User token expired", err.message)
        except (unauthorizedRequest, UserNotFound) as err:
            if request.get_header("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.get_header("X-Auth-User"))
            logging.debug(err.message)                
            raise falcon.HTTPUnauthorized("Unauthorized", err.message)
        except requests.HTTPError as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError(str(err), err.response.text)
        except requests.ConnectionError as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError(str(err), "Connection error")        
        except Exception as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError('Contact the admin. ', str(err))

class UserAuth(object):
    def on_post(self, request, response):
        try:
            credentials = json.loads(request.stream.read().decode())
            
            token = UserAuthentication().authenticateUserFromCredentials(credentials)
            
            response.body = token
            response.status = falcon.HTTP_200
        
        except wrongRequest as err:
            logging.exception(err)
            raise falcon.HTTPBadRequest("Bad Request", err.description)
        except (unauthorizedRequest, UserNotFound) as err:
            if request.get_header("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.get_header("X-Auth-User"))
            raise falcon.HTTPUnauthorized("Unauthorized", err.message)
        except Exception as err:
            logging.exception(err)
            raise falcon.HTTPInternalServerError('Contact the admin. ', str(err))