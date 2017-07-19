import logging

from flask import Flask

from do_core.api.api import root_blueprint
from do_core.api.nffg import api as nffg_api
from do_core.api.user import api as user_api


from do_core.config import Configuration
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
print("Welcome to the Openstack Domain Orchestrator")

# Rest application
if nffg_api is not None and user_api is not None:
    app = Flask(__name__)
    app.register_blueprint(root_blueprint)
    logging.info("Flask Successfully started")

Messaging().publishDomainDescription()


