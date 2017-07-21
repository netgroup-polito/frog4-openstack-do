class UserNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(UserNotFound, self).__init__(message)
        
    def get_mess(self):
        return self.message


class TenantNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(TenantNotFound, self).__init__(message)
        
    def get_mess(self):
        return self.message


class StackError(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(StackError, self).__init__(message)
        
    def get_mess(self):
        return self.message


class WrongConfigurationFile(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(WrongConfigurationFile, self).__init__(message)
        
    def get_mess(self):
        return self.message


class sessionNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(sessionNotFound, self).__init__(message)
        
    def get_mess(self):
        return self.message


class wrongRequest(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(wrongRequest, self).__init__(message)
    
    def get_mess(self):
        return self.message


class unauthorizedRequest(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(unauthorizedRequest, self).__init__(message)
    
    def get_mess(self):
        return self.message


class UserTokenExpired(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(UserTokenExpired, self).__init__(message)
    
    def get_mess(self):
        return self.message


class GraphError(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(GraphError, self).__init__(message)
    
    def get_mess(self):
        return self.message


class GraphNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(GraphNotFound, self).__init__(message)
    
    def get_mess(self):
        return self.message


class EndpointNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(EndpointNotFound, self).__init__(message)
    
    def get_mess(self):
        return self.message


class VNFRepositoryError(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(VNFRepositoryError, self).__init__(message)

    def get_mess(self):
        return self.message


'''
***************************************
*         ONOS/ODL Exceptions         *
***************************************
'''

class OnosInternalError(Exception):
    def __init__(self, message):
        self.message = message
            # Call the base class constructor with the parameters it needsù
        super(OnosInternalError, self).__init__(message)

    def get_mess(self):
        return self.message


class OVSDBNodeNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(OVSDBNodeNotFound, self).__init__(message)

    def get_mess(self):
        return self.message


class BridgeNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(BridgeNotFound, self).__init__(message)

    def get_mess(self):
        return self.message


class PortNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(PortNotFound, self).__init__(message)

    def get_mess(self):
        return self.message


class NoGraphFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(NoGraphFound, self).__init__(message)

    def get_mess(self):
        return self.message