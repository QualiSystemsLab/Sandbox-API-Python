"""
Sandbox controller context manager to manage the lifecyle of setup and teardown
- start sandbox on context enter, end sandbox on context exit
- cache setup / teardown duration and errors
- components object member
- async commands executor member
"""
import logging
from typing import List

from cloudshell.sandbox_rest.api import SandboxRestApiSession, CommandInputParam
from cloudshell.sandbox_rest import exceptions
from cloudshell.sandbox_rest import model
from cloudshell.sandbox_rest.async_commands import AsyncCommandExecutor
from cloudshell.sandbox_rest.components import SandboxComponents
from dataclasses import dataclass
from timeit import default_timer


@dataclass
class SandboxStartRequest:
    blueprint_id: str
    sandbox_name: str = ""
    duration: str = "PT2H0M"
    bp_params: List[CommandInputParam] = None
    permitted_users: List[str] = None
    max_polling_minutes: int = 20
    polling_frequency_seconds: int = 30
    polling_log_level: int = logging.DEBUG


@dataclass
class TeardownSettings:
    max_polling_minutes: int = 20
    polling_frequency_seconds: int = 30
    polling_log_level: int = logging.DEBUG


class SandboxControllerContext:
    def __init__(self, api: SandboxRestApiSession, sandbox_id: str = None,sandbox_request: SandboxStartRequest = None,
                 teardown_settings = TeardownSettings(), logger: logging.Logger = None):
        self.api = api
        self.sandbox_id = sandbox_id
        self.sandbox_request = sandbox_request
        self.teardown_settings = teardown_settings
        self.logger = logger
        self.components = SandboxComponents()
        self.async_executor = AsyncCommandExecutor()
        self.setup_duration_seconds: int = None
        self.teardown_duration_seconds: int = None
        self.setup_errors: List[model.SandboxEvent] = None
        self.teardown_errors: List[model.SandboxEvent] = None
        self._validate_init()

    def _validate_init(self):
        if not self.sandbox_request and not self.sandbox_id:
            raise ValueError("Must supply either an existing sandbox id or a SandboxStartRequest object")

    def _info_log(self, msg: str):
        if self.logger:
            self.logger.info(msg)

    def _debug_log(self, msg: str):
        if self.logger:
            self.logger.debug(msg)

    def _error_log(self, msg: str):
        if self.logger:
            self.logger.error(msg)

    def launch_sandbox(self):
        if self.sandbox_id:
            self._debug_log(f"launch sandbox called for existing sandbox '{self.sandbox_id}'. Returning")
            return

        if not self.sandbox_request:
            raise ValueError("No StartSandboxRequest object passed to init")

        start_response = self.api.start_sandbox(blueprint_id=self.sandbox_request.blueprint_id,
                                                sandbox_name=self.sandbox_request.sandbox_name,
                                                duration=self.sandbox_request.duration,
                                                bp_params=self.sandbox_request.bp_params,
                                                permitted_users=self.sandbox_request.permitted_users)
        self.sandbox_id = start_response.id
        self._info_log(f"Sandbox '{self.sandbox_id}' started.")
        self._info_log("Starting blocking sandbox and polling...")
        start = default_timer()
        try:
            self.api.poll_sandbox_setup(reservation_id=self.sandbox_id,
                                        max_polling_minutes=self.sandbox_request.max_polling_minutes,
                                        polling_frequency_seconds=self.sandbox_request.polling_frequency_seconds,
                                        log_level=self.sandbox_request.polling_log_level)
        except exceptions.SetupFailedException as e:
            self.setup_errors = e.error_events
            setup_duration_seconds = default_timer() - start
            self._error_log(f"Sandbox '{self.sandbox_id}' setup FAILED after {setup_duration_seconds} seconds")
            self._error_log(str(e))
            raise

        setup_duration_seconds = default_timer() - start
        self._info_log(f"Sandbox '{self.sandbox_id}' setup completed after {setup_duration_seconds} seconds")
        self.setup_duration_seconds = setup_duration_seconds
        self.refresh_components()

    def teardown_sandbox(self):
        if not self.sandbox_id:
            self._debug_log("Trying to start teardown, but no sandbox ID found. Returning")
            return

        if self.teardown_duration_seconds:
            self._debug_log(f"Teardown has already ran for sandbox '{self.sandbox_id}'. Returning")

        self._info_log(f"starting blocking teardown of sandbox '{self.sandbox_id}'")
        start = default_timer()
        try:
            self.api.stop_sandbox(sandbox_id=self.sandbox_id,
                                  poll_teardown=True,
                                  max_polling_minutes=self.teardown_settings.max_polling_minutes,
                                  polling_frequency_seconds=self.teardown_settings.polling_frequency_seconds,
                                  polling_log_level=self.teardown_settings.polling_log_level)
        except exceptions.TeardownFailedException as e:
            self.teardown_errors = e.error_events
            teardown_duration_seconds = default_timer() - start
            self._error_log(f"Sandbox '{self.sandbox_id}' setup FAILED after {teardown_duration_seconds} seconds")
            self._error_log(str(e))
            raise

        teardown_duration_seconds = default_timer() - start
        self._info_log(f"Sandbox '{self.sandbox_id}' teardown completed after {teardown_duration_seconds} seconds")
        self.teardown_duration_seconds = teardown_duration_seconds
        self.refresh_components()

    def __enter__(self):
        """ start sandbox """
        self.launch_sandbox()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ end sandbox """
        self.teardown_sandbox()
        return self

    def refresh_components(self):
        self.components.refresh_components(self.api, self.sandbox_id)


if __name__ == "__main__":
    controller = SandboxControllerContext()
    controller.async_executor
