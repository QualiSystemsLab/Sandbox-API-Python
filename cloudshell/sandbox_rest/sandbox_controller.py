import json
import logging
from typing import List

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession, InputParam
from cloudshell.sandbox_rest.helpers import polling_helpers as poll_help


class SandboxSetupError(Exception):
    """ When sandbox has error during setup """
    pass


class SandboxTeardownError(Exception):
    """ When sandbox has error during setup """
    pass


class CommandFailedException(Exception):
    pass


# TODO:
# add context manager methods
# review design of class
# add logger
# publish env vars


class SandboxRestController:
    def __init__(self, api: SandboxRestApiSession, sandbox_id="", log_file_handler=False):
        self.api = api
        self.sandbox_id = sandbox_id
        self.logger = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def start_sandbox_and_poll(self, blueprint_id: str, sandbox_name="", duration="PT1H30M",
                               bp_params: List[InputParam] = None, permitted_users: List[str] = None,
                               max_polling_minutes=30) -> dict:
        """ Start sandbox, poll for result, get back sandbox info """
        start_response = self.api.start_sandbox(blueprint_id, sandbox_name, duration, bp_params, permitted_users)
        sb_id = start_response["id"]
        sandbox_details = poll_help.poll_sandbox_setup(self.api, sb_id, max_polling_minutes,
                                                       polling_frequency_seconds=30)

        sandbox_state = sandbox_details["state"]
        stage = sandbox_details["setup_stage"]
        name = sandbox_details["name"]

        if "error" in sandbox_state.lower():
            activity_errors = self._get_all_activity_errors(sb_id)

            # TODO: print this? log it? or dump into exception message?
            if activity_errors:
                print(f"=== Activity Feed Errors ===\n{json.dumps(activity_errors, indent=4)}")

            err_msg = (f"Sandbox '{name}' Error during SETUP.\n"
                       f"Stage: '{stage}'. State '{sandbox_state}'. Sandbox ID: '{sb_id}'")
            raise SandboxSetupError(err_msg)
        return sandbox_details

    def stop_sandbox_and_poll(self, sandbox_id: str, max_polling_minutes=30) -> dict:
        self.api.stop_sandbox(sandbox_id)
        sandbox_details = poll_help.poll_sandbox_teardown(self.api, sandbox_id, max_polling_minutes,
                                                          polling_frequency_seconds=30)
        sandbox_state = sandbox_details["state"]
        stage = sandbox_details["setup_stage"]
        name = sandbox_details["name"]

        if "error" in sandbox_state.lower():
            tail_error_count = 5
            tailed_errors = self.api.get_sandbox_activity(sandbox_id, error_only=True, tail=tail_error_count)["events"]
            print(f"=== Last {tail_error_count} Errors ===\n{json.dumps(tailed_errors, indent=4)}")
            err_msg = (f"Sandbox '{name}' Error during SETUP.\n"
                       f"Stage: '{stage}'. State '{sandbox_state}'. Sandbox ID: '{sandbox_id}'")
            raise SandboxTeardownError(err_msg)
        return sandbox_details

    def _get_all_activity_errors(self, sandbox_id):
        activity_results = self.api.get_sandbox_activity(sandbox_id, error_only=True)
        return activity_results["events"]

    def publish_sandbox_id_to_env_vars(self):
        pass
