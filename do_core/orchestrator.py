'''
Created on Apr 15, 2016

@author: stefanopetrangeli
'''
from flask.views import MethodView
from flask import request
import logging
import requests
import json

from sqlalchemy.orm.exc import NoResultFound
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG

from do_core.controller import OpenstackOrchestratorController
from do_core.userAuthentication import UserAuthentication
from do_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, ingoingFlowruleMissing, ManifestValidationError, UserNotFound, UserTokenExpired

class NFFGStatus(MethodView):
    def get(self, nffg_id):
        """
        Get the status of a graph
        a
        ---
        tags:
          - NF-FG
        produces:
          - application/json             
        parameters:
          - name: nffg_id
            in: path
            description: NFFG to be retrieved
            type: string            
            required: true
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string
                    
        responses:
          401:
            description: Unauthorized
          404:
            description: Graph not found
          500:
            description: Internal Error
        """           
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
                   
            controller = OpenstackOrchestratorController(user_data)
            return controller.getStatus(nffg_id)
                        
        except NoResultFound:
            logging.exception("EXCEPTION - NoResultFound")
            return ("EXCEPTION - NoResultFound", 404)
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)
        except sessionNotFound as err:
            logging.exception(err.message)
            return (err.message, 404)
        except ManifestValidationError as err:
            logging.exception(err.message)
            return ('ManifestValidationError '+err.message, 500) 
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401) 
        except Exception as ex:
            logging.exception(ex)
            return ("Contact the admin "+ str(err), 500)
      
class OpenstackOrchestrator(MethodView):
    '''
    Admin class that intercept the REST call through the WSGI server
    '''
    def delete(self, nffg_id):
        """
        Delete a graph
        ---
        tags:
          - NF-FG   
        parameters:
          - name: nffg_id
            in: path
            description: NFFG to be retrieved
            required: true
            type: string            
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string            
        responses:
          401:
            description: Unauthorized
          404:
            description: Graph not found
          500:
            description: Internal Error
        """        
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
                   
            controller = OpenstackOrchestratorController(user_data)
            controller.delete(nffg_id)
            
            return ("Session deleted")
            
        except NoResultFound:
            logging.exception("EXCEPTION - NoResultFound")
            return ("EXCEPTION - NoResultFound", 404)
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)
        except sessionNotFound as err:
            logging.exception(err.message)
            return (err.message, 404)
        except ManifestValidationError as err:
            logging.exception(err.message)
            return ('ManifestValidationError '+err.message, 500) 
        except UserTokenExpired as err:
            logging.debug("User token is expired")
            return ("User token expired", 401)       
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401) 
        except Exception as ex:
            logging.exception(ex)
            return ("Contact the admin "+ str(err), 500)
    
    def get(self, nffg_id):
        """
        Get a graph
        Returns an already deployed graph
        ---
        tags:
          - NF-FG
        produces:
          - application/json          
        parameters:
          - name: nffg_id
            in: path
            description: NFFG to be retrieved
            required: true
            type: string            
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string            
        responses:
          401:
            description: Unauthorized
          404:
            description: Graph not found
          500:
            description: Internal Error
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
                   
            controller = OpenstackOrchestratorController(user_data)
            return controller.get(nffg_id)
            
        except NoResultFound:
            logging.exception("EXCEPTION - NoResultFound")
            return ("EXCEPTION - NoResultFound", 404)
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)
        except requests.ConnectionError as err:
            logging.exception(err)
            return (str(err), 500)       
        except sessionNotFound as err:
            logging.exception(err.message)
            return (err.message, 404)
        except ManifestValidationError as err:
            logging.exception(err.message)
            return ('ManifestValidationError '+err.message, 500) 
        except UserTokenExpired as err:
            logging.debug("User token is expired")
            return ("User token expired", 401)       
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)   
        except Exception as ex:
            logging.exception(ex)
            return ("Contact the admin "+ str(err), 500)
        
    def put(self, nffg_id = None):
        """
        Put a graph
        Deploy a graph
        ---
        tags:
          - NF-FG
        parameters:
          - name: nffg_id
            in: path
            description: ID of the graph
            type: string            
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string
          - name: NF-FG
            in: body
            description: Graph to be deployed
            required: true
            type: string
        responses:
          401:
            description: Unauthorized
          400:
            description: Bad request
          500:
            description: Internal Error
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
            
            nffg_dict = json.loads(request.data.decode())
            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)
            
            controller = OpenstackOrchestratorController(user_data)
            return (controller.put(nffg), 202, {'ContentType':'application/json'})
            
        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
        except UserTokenExpired as err:
            logging.debug("User token is expired")
            return ("User token expired", 401)            
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)        
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)
        except requests.ConnectionError as err:
            logging.exception(err)
            return (str(err), 500)
        except Exception as err:
            logging.exception(err)
            return ("Contact the admin "+ str(err), 500)

class UserAuth(MethodView):
    def post(self):
        """
        Perform the login
        Given the credentials it returns the token associated to that user
        ---
        tags:
          - NF-FG
        parameters:
          - in: body
            name: body
            schema:
              id: login
              required:
                - username
                - password
              properties:
                username:
                  type: string
                  description:  username
                password:
                  type: string
                  description: password

        responses:
          401:
           description: Login failed
          400:
           description: Bad request
          500:
            description: Internal Error                
        """
        try:
            credentials = json.loads(request.data.decode())
            
            token = UserAuthentication().authenticateUserFromCredentials(credentials)
            return token
        
        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401) 
        except Exception as err:
            logging.exception(err)
            return ("Contact the admin "+ str(err), 500)
