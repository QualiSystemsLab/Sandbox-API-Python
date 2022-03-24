class SandboxRestException(Exception):
    """ Base Exception Class inside Rest client class """


class SandboxRestAuthException(SandboxRestException):
    """ Failed login action """


class OrchestrationPollingTimeout(SandboxRestException):
    pass


class CommandPollingTimeout(SandboxRestException):
    pass


class SetupFailedException(SandboxRestException):
    pass


class CommandExecutionFailed(SandboxRestException):
    pass
