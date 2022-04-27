from typing import List

from cloudshell.sandbox_rest import model


class SandboxRestException(Exception):
    """ Base Exception Class inside Rest client class """


class SandboxRestAuthException(SandboxRestException):
    """ Failed login action """


class OrchestrationPollingTimeout(SandboxRestException):
    pass


class CommandPollingTimeout(SandboxRestException):
    pass


class FailedOrchestrationException(SandboxRestException):
    def __init__(self, message: str, error_events: List[model.SandboxEvent] = None):
        self.message = message
        self.error_events = error_events or []
        super().__init__(message)

    def events_to_json(self):
        return model.models_to_json(self.error_events)

    def __str__(self):
        return f"{self.message}\n{self.events_to_json()}"


class SetupFailedException(FailedOrchestrationException):
    def __init__(self, message: str, error_events: List[model.SandboxEvent] = None):
        super().__init__(message, error_events)


class TeardownFailedException(FailedOrchestrationException):
    def __init__(self, message: str, error_events: List[model.SandboxEvent] = None):
        super().__init__(message, error_events)


class CommandExecutionFailed(SandboxRestException):
    pass
