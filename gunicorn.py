import sys, os
from subprocess import call
from do_core.config import Configuration

conf_file = None
i = 1
for param in sys.argv:
    if param == "--d":
        if len(sys.argv) > i:
            conf_file = sys.argv[i]
            break
        else:
            print ("Wrong params usage --d [conf-file]")
            exit(1)
    i = i + 1
if conf_file is not None:
    os.environ.setdefault("FROG4_OPENSTACK_CONF", conf_file)
conf = Configuration()
ip = conf.ORCH_IP
port = conf.ORCH_PORT
address = str(ip) +":"+str(port)

call("gunicorn -b "+ address +" -t 500 main:app", shell=True)
