import logging
import os
import inspect
import json
import pdb

from flask import Flask
from flasgger import Swagger

from do_core.config import Configuration
from do_core.orchestrator import OpenstackOrchestrator, NFFGStatus, UserAuth
from do_core.messaging import Messaging

conf = Configuration()

# set log level
if conf.DEBUG is True:
    log_level = logging.DEBUG
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
    sqlalchemy_log = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_log.setLevel(logging.WARNING)
elif conf.VERBOSE is True:
    log_level = logging.INFO
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
else:
    log_level = logging.WARNING

#format = '%(asctime)s %(filename)s %(funcName)s %(levelname)s %(message)s'
log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s'

logging.basicConfig(filename=conf.LOG_FILE, level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.debug("Openstack Domain Orchestrator Starting")
pdb.set_trace()
print("Welcome to the Openstack Domain Orchestrator")

app = Flask(__name__)

swagger_config = {
    "swagger_version": "2.0",
    "title": "OpenStack Domain Orchestrator API",
    "headers": [
         ('Access-Control-Allow-Origin', '*')
    ],
    "specs": [
        {
            "version": "1.0.0",
            "title": "OpenStack DO API",
            "endpoint": 'v1_spec',
            "route": '/v1/spec',
        }
    ],
        "static_url_path": "/apidocs",
        "static_folder": "swaggerui",
        "specs_route": "/specs"
}

Swagger(app, config=swagger_config)

orch = OpenstackOrchestrator.as_view('NF-FG')
app.add_url_rule(
    '/NF-FG/<nffg_id>',
    view_func=orch,
    methods=["GET", "PUT", "DELETE"]
)

login = UserAuth.as_view('login')
app.add_url_rule(
    '/login',
    view_func=login,
    methods=["POST"]
)

nffg_status = NFFGStatus.as_view('NFFGStatus')
app.add_url_rule(
    '/NF-FG/status/<nffg_id>',
    view_func=nffg_status,
    methods=["GET"]
)

Messaging().publishDomainDescription()

logging.info("Flask Successfully started")
