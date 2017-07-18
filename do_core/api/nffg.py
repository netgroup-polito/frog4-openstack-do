import logging
import requests
import json


from flask_restplus import Resource
from flask import request, Response

from sqlalchemy.orm.exc import NoResultFound
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG
from nffg_library.exception import NF_FGValidationError

from do_core.controller import OpenstackOrchestratorController
from do_core.userAuthentication import UserAuthentication
from do_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, UserNotFound, UserTokenExpired



from do_core.api.api import api

nffg_ns = api.namespace('NF-FG', 'NFFG Resource')


@nffg_ns.route('/<nffg_id>', methods=['PUT','DELETE','GET'],
               doc={'params': {'nffg_id': {'description': 'The graph ID', 'in': 'path'}}})
@api.doc(responses={404: 'Graph not found'})
class NFFGResource(Resource):

    counter = 1

    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.param("NFFG", "Graph to be deployed", "body", type="string", required=True)
    @nffg_ns.response(201, 'Graph correctly updated.')
    @nffg_ns.response(400, 'Bad request.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(409, 'The graph is valid ')
    @nffg_ns.response(500, 'Internal Error.')
    def put(self, nffg_id):
        """
        Update a Network Functions Forwarding Graph
        Update a graph
        """

        pass
    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.response(200, 'Graph deleted.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def delete(self, nffg_id):
        """
        Delete a graph
        """
        pass
    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.response(200, 'Graph retrieved.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def get(self, nffg_id=None):
        """
        Returns an already deployed graph
        Get a graph
        """
        pass

@nffg_ns.route('/status/<nffg_id>', methods=['GET'], doc={'params': {'nffg_id': {'description':
                                                                                     'The Graph ID to be retrieved'}}})
@api.doc(responses={404: 'Graph not found'})
class NFFGStatusResource(Resource):

    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.response(200, 'Status correctly retrieved.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def get(self, nffg_id):
        """
        Get the status of a graph

        """
        pass



@nffg_ns.route('/', methods=['POST','GET'])
class UpperLayerOrchestrator(Resource):

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
        return NFFGResource.get(self)

    counter = 1

    @nffg_ns.param("X-Auth-Token", "Authentication Token", "header", type="string", required=True)
    @nffg_ns.param("NFFG", "Graph to be deployed", "body", type="string", required=True)
    @nffg_ns.response(201, 'Graph correctly deployed and returning the graph id.')
    @nffg_ns.response(400, 'Bad request.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(409, 'The graph is valid but does not have a feasible deployment in the current network.')
    @nffg_ns.response(500, 'Internal Error.')
    def post(self):
        """
        Create a New Network Functions Forwarding Graph
        Deploy a graph
        """

        pass