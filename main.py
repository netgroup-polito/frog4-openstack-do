import falcon
import logging
import os
import inspect

from threading import Thread
from do_core.config import Configuration
from do_core.orchestrator import OpenstackOrchestrator, NFFGStatus, UserAuth
#from do_core.dd_server import DD_Server

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

# Falcon starts
app = falcon.API()

upper_layer_API = OpenstackOrchestrator()
nffg_status = NFFGStatus()
user_auth = UserAuth()


app.add_route('/NF-FG', upper_layer_API)
app.add_route('/NF-FG/{nffg_id}', upper_layer_API)
app.add_route('/NF-FG/status/{nffg_id}', nffg_status)
app.add_route('/login', user_auth)


"""
base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
dd_server = DD_Server(conf.DD_NAME, conf.BROKER_ADDRESS, conf.DD_CUSTOMER, conf.DD_KEYFILE)
thread = Thread(target=dd_server.start)
thread.start()
"""
logging.info("Falcon Successfully started")
