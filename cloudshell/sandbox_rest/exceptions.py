class SandboxRestException(Exception):
    """ General exception to raise inside Rest client class """
    pass


class SandboxRestAuthException(Exception):
    """ Failed auth actions """
    pass


class SandboxRestInitException(ValueError):
    """ Failed auth actions """
    pass
