import logging

VERSION = "0.1.6"

class MethodNotFound(Exception):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return 'service method: %s not-found' % repr(self.name)
    
class TypeNotFound(Exception):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return 'WSDL type: %s not-found' % repr(self.name)
    
class BuildError(Exception):
    def __init__(self, type):
        self.type = type
    def __str__(self):
        return \
            """
            An error occured while building a instance of (%s).  As a result
            the object you requested could not be constructed.  It is recommended
            that you construct the type manually uisng a Property object.
            Please notify the project mantainer of this error.
            """ % self.type
    
class WebFault(Exception):
    def __init__(self, type):
        self.type = type
    def __str__(self):
        return 'service provider raised fault %s\n' % repr(self.type)

def logger(name=None):
    if name is None:
        return logging.getLogger()
    fmt =\
        '%(asctime)s {%(process)d} (%(filename)s, %(lineno)d) [%(levelname)s] %(message)s'
    logger = logging.getLogger('suds.%s' % name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        __handler = logging.StreamHandler()
        __handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(__handler)
    return logger
