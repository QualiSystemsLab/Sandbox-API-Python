"""
Sandbox controller context manager to manage the lifecyle of setup and teardown
- start sandbox on context enter, end sandbox on context exit
- cache setup / teardown duration and errors
- components object member
- async commands executor member
"""
import logging

from cloudshell.sandbox_rest.api import SandboxRestApiSession
from cloudshell.sandbox_rest.async_commands import AsyncCommandExecutor
from cloudshell.sandbox_rest.components import SandboxComponents


class SandboxStartRequest:
    pass


class SandboxControllerContext:
    def __init__(self, api: SandboxRestApiSession, sandbox_request: SandboxStartRequest = None, sandbox_id: str = None,
                 logger: logging.Logger = None):
        self.api = api
        self.sandbox_request = sandbox_request
        self.sandbox_id = sandbox_id
        self.logger = logger
        self.components = SandboxComponents()
        self.async_executor = AsyncCommandExecutor()
        self.setup_duration_seconds: int = None
        self.teardown_duration_seconds: int = None
        self.setup_errors = None
        self.teardown_errors = None

    def __enter__(self):
        """ start sandbox """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ end sandbox """
        return self

    def refresh_components(self):
        self.components.refresh_components(self.api, self.sandbox_id)


if __name__ == "__main__":
    controller = SandboxControllerContext()