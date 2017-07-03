try:
    from .doubledecker.clientSafe import ClientSafe
except ImportError:
    from doubledecker.clientSafe import ClientSafe

import json
import logging
from do_core.config import Configuration
from threading import Thread
from do_core.resource_description import ResourceDescription

DD_NAME = Configuration().DD_NAME
DD_CUSTOMER = Configuration().DD_CUSTOMER
DD_KEYFILE = Configuration().DD_KEYFILE
BROKER_ADDRESS = Configuration().BROKER_ADDRESS
DOMAIN_DESCRIPTION_TOPIC = Configuration().DOMAIN_DESCRIPTION_TOPIC
DOMAIN_DESCRIPTION_FILE = Configuration().DOMAIN_DESCRIPTION_FILE

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class DD_client(ClientSafe):

    def __init__(self, name, dealerurl, customer, keyfile, topic, message):
        super().__init__(name=name, dealerurl=dealerurl, customer=customer, keyfile=keyfile)
        self._registered = False
        self.topic = topic
        self.message = message
        
    def on_data(self, dest, msg):
        print(dest, " sent", msg)

    def on_pub(self, src, topic, msg):
        msgstr = "PUB %s from %s: %s" % (str(topic), str(src), str(msg))
        print(msgstr)

    def on_reg(self):
        self._registered = True
        self.publish(self.topic, self.message)

    def on_discon(self):
        pass

    def on_error(self):
        pass

    def unsubscribe(self, topic, scope):
        pass
    
    @property
    def REGISTERED(self):
        return self._registered

class Messaging(object, metaclass=Singleton):
    def __init__(self):
        self.dd_class = None
        self.working_thread = None
        self.first_start = True
        
    def _cold_start(self):
        message = self.readDomainDescriptionFile()
        self.dd_class = DD_client(name=DD_NAME, dealerurl=BROKER_ADDRESS, customer=DD_CUSTOMER, keyfile=DD_KEYFILE, topic=DOMAIN_DESCRIPTION_TOPIC, message=message)
        self.working_thread = Thread(target=self.dd_class.start)
        self.working_thread.start()

    def publishDomainDescription(self):
        if self.first_start is True:
            self._cold_start()
            self.first_start = False
            return
        message = self.readDomainDescriptionFile()
        try:
            self.dd_class.publish(DOMAIN_DESCRIPTION_TOPIC, message)
        except ConnectionError:
            #TODO. raise proper exception
            raise Exception("DD client not registered") from None
        
    def readDomainDescriptionFile(self):
        return json.dumps(ResourceDescription(DOMAIN_DESCRIPTION_FILE).dict)

    
    
