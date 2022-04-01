"""
Sandbox controller context manager to manage the lifecyle of setup and teardown
"""


from cloudshell.sandbox_rest.api import SandboxRestApiSession


class SandboxControllerContext:
    def __init__(self, api: SandboxRestApiSession, sandbox_id: str = None):
        self.api = api
        self.sandbox_id = sandbox_id

    def __enter__(self):
        """ start sandbox """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ end sandbox """
        return self
