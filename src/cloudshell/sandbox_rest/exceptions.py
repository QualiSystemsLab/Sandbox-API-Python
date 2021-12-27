class SandboxRestException(Exception):
    """ Base Exception Class inside Rest client class """


class SandboxRestAuthException(SandboxRestException):
    """ Failed login action """
