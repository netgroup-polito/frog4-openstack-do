'''
Created on Apr 15, 2016

@author: stefanopetrangeli
'''
from flask.views import MethodView
from flask import request, Response
import logging
import requests
import json

from sqlalchemy.orm.exc import NoResultFound
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG
from nffg_library.exception import NF_FGValidationError

from do_core.controller import OpenstackOrchestratorController
from do_core.userAuthentication import UserAuthentication
from do_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, UserNotFound, UserTokenExpired

class NFFGStatus(MethodView):
    def get(self, nffg_id):
        """
        Get the status of a graph
        ---
        tags:
          - NF-FG
        produces:
          - application/json             
        parameters:
          - name: nffg_id
            in: path
            description: Graph ID to be retrieved
            type: string            
            required: true
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string
                    
        responses:
          200:
            description: Status correctly retrieved        
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
            resp = Response(response=controller.getStatus(nffg_id), status=200, mimetype="application/json")
            return resp        
                        
        except NoResultFound:
            logging.exception("EXCEPTION - NoResultFound")
            return ("EXCEPTION - NoResultFound", 404)
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)
        except sessionNotFound as err:
            logging.exception(err.message)
            return (err.message, 404)
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)        
        except Exception as err:
            logging.exception(err)
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
            description: Graph ID to be deleted
            required: true
            type: string            
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string            
        responses:
          200:
            description: Graph deleted        
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
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)       
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401) 
        except Exception as err:
            logging.exception(err)
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
            description: Graph ID to be retrieved
            required: true
            type: string            
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string            
        responses:
          200:
            description: Graph retrieved        
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
            resp = Response(response=controller.get(nffg_id), status=200, mimetype="application/json")
            return resp
            
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
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)  
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)   
        except Exception as err:
            logging.exception(err)
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
            required: true       
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string
          - name: NF-FG
            in: body
            description: Graph to be deployed
            required: true
            schema:
                type: string
        responses:
          202:
            description: Graph correctly deployed        
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
            return (controller.put(nffg), 202)
            
        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)          
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
        except NF_FGValidationError as err:
            logging.exception(err)            
            return ("NF-FG Validation Error: "+ err.message, 400)             
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
          200:
            description: Login successfully performed              
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
            resp_token = Response(response = token, status=200,
                                  mimetype="application/token")
            return resp_token
        
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
