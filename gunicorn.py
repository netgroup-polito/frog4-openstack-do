from subprocess import call
from do_core.config import Configuration

conf = Configuration()
ip = conf.ORCH_IP
port = conf.ORCH_PORT
address = str(ip) +":"+str(port)

call("gunicorn -b "+ address +" -t 500 main:app", shell=True)
