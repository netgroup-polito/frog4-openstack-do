import logging
import requests
import json

from flask_restplus import Resource
from flask import request, Response
from do_core.api.api import api
from sqlalchemy.orm.exc import NoResultFound
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG
from nffg_library.exception import NF_FGValidationError

from do_core.controller import OpenstackOrchestratorController
from do_core.userAuthentication import UserAuthentication
from do_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, UserNotFound, UserTokenExpired

nffg_ns = api.namespace('NF-FG', 'NFFG Resource')

@nffg_ns.route('/<nffg_id>', methods=['PUT','DELETE','GET'],
               doc={'params': {'nffg_id': {'description': 'The graph ID', 'in': 'path'}}})
@api.doc(responses={404: 'Graph not found'})
class OpenstackOrchestrator(Resource):

    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.param("NFFG", "Graph to be updated", "body", type="string", required=True)
    @nffg_ns.response(201, 'Graph correctly updated.')
    @nffg_ns.response(400, 'Bad request.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def put(self, nffg_id):
        """
        Update a Network Functions Forwarding Graph
        Update a graph
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)

            nffg_dict = json.loads(request.data.decode())
            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)

            controller = OpenstackOrchestratorController(user_data)
            return (controller.put(nffg, nffg_id), 201)

        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user " + request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
        except NF_FGValidationError as err:
            logging.exception(err)
            return ("NF-FG Validation Error: " + err.message, 400)
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)
        except requests.ConnectionError as err:
            logging.exception(err)
            return (str(err), 500)
        except Exception as err:
            logging.exception(err)
            return ("Contact the admin " + str(err), 500)

    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.response(200, 'Graph deleted.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def delete(self, nffg_id):
        """
        Delete a graph
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
                logging.debug("Unauthorized access attempt from user " + request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
        except Exception as err:
            logging.exception(err)
            return ("Contact the admin " + str(err), 500)

    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.response(200, 'Graph retrieved.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def get(self, nffg_id=None):
        """
        Returns an already deployed graph
        Get a graph
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
                logging.debug("Unauthorized access attempt from user " + request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
        except Exception as err:
            logging.exception(err)
            return ("Contact the admin " + str(err), 500)


@nffg_ns.route('/status/<nffg_id>', methods=['GET'], doc={'params': {'nffg_id': {'description':
                                                                                     'The Graph ID to be retrieved'}}})
@api.doc(responses={404: 'Graph not found'})
class NFFGStatus(Resource):

    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.response(200, 'Status correctly retrieved.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def get(self, nffg_id):
        """
        Get the status of a graph

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
                logging.debug("Unauthorized access attempt from user " + request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)
        except Exception as err:
            logging.exception(err)
            return ("Contact the admin " + str(err), 500)


@nffg_ns.route('/', methods=['POST','GET'])
class NFFGResource(Resource):

    # This class is necessary because there is a conflict in the swagger documentation of get and put operations

    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.response(200, 'List retrieved.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(404, 'Graph not found.')
    @nffg_ns.response(500, 'Internal Error.')
    def get(self):
        """
        Get the list of graphs currently deployed
        Returns the list of the active graphs
        """
        return OpenstackOrchestrator.get(request)

    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.param("NFFG", "Graph to be deployed", "body", type="string", required=True)
    @nffg_ns.response(201, 'Graph correctly deployed and returning the graph id.')
    @nffg_ns.response(400, 'Bad request.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def post(self):
        """
        Create a New Network Functions Forwarding Graph
        Deploy a graph
        """

        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)

            nffg_dict = json.loads(request.data.decode())
            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)

            controller = OpenstackOrchestratorController(user_data)
            return (controller.post(nffg), 202)

        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user " + request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
        except NF_FGValidationError as err:
            logging.exception(err)
            return ("NF-FG Validation Error: " + err.message, 400)
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)
        except requests.ConnectionError as err:
            logging.exception(err)
            return (str(err), 500)
        except Exception as err:
            logging.exception(err)
            return ("Contact the admin " + str(err), 500)
