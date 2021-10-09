from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession, InputParam
from cloudshell.sandbox_rest.helpers.polling_helpers import poll_sandbox_setup, poll_sandbox_teardown, \
    poll_execution_for_completion, SandboxStates, SANDBOX_SETUP_STATES, SANDBOX_ACTIVE_STATES
from cloudshell.sandbox_rest.sandbox_components import SandboxRestComponents
import json
from typing import List
from timeit import default_timer


class SandboxSetupError(Exception):
    """ When sandbox has error during setup """
    pass


class SandboxTeardownError(Exception):
    """ When sandbox has error during setup """
    pass


class CommandFailedException(Exception):
    pass


class SandboxRestController:
    def __init__(self, api: SandboxRestApiSession, sandbox_id="", disable_prints=False):
        self.api = api
        self.sandbox_id = sandbox_id
        self.components = SandboxRestComponents()
        self.setup_finished = False
        self.sandbox_ended = False
        self.setup_errors: List[dict] = None
        self.teardown_errors: List[dict] = None
        self.disable_prints = disable_prints

        # when passing in existing sandbox id update instance state, otherwise let "start sandbox" handle it
        if self.sandbox_id:
            self._handle_sandbox_id_on_init()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            err_msg = f"Exiting sandbox scope with error. f{exc_type}: {exc_val}"
            self._print(err_msg)

    def _handle_sandbox_id_on_init(self):
        self.update_components()
        self.update_state_flags()

    def update_components(self):
        components = self.api.get_sandbox_components(self.sandbox_id)
        self.components.refresh_components(components)

    def update_state_flags(self):
        details = self.api.get_sandbox_details(self.sandbox_id)
        sandbox_state = details["state"]
        if sandbox_state not in SANDBOX_SETUP_STATES:
            self.setup_finished = True
        elif sandbox_state not in SANDBOX_ACTIVE_STATES:
            self.sandbox_ended = True

    def _print(self, message):
        if not self.disable_prints:
            print(message)

    def start_sandbox_and_poll(self, blueprint_id: str, sandbox_name="", duration="PT1H30M",
                               bp_params: List[InputParam] = None, permitted_users: List[str] = None,
                               max_polling_minutes=30, raise_setup_exception=True) -> dict:
        """ Start sandbox, poll for result, get back sandbox info """
        if self.sandbox_id:
            raise ValueError(f"Sandbox already has id '{self.sandbox_id}'.\n"
                             f"Start blueprint with new sandbox controller instance")

        self._print(f"Starting blueprint {blueprint_id}")
        start = default_timer()
        start_response = self.api.start_sandbox(blueprint_id, sandbox_name, duration, bp_params, permitted_users)
        self.sandbox_id = start_response["id"]
        sandbox_details = poll_sandbox_setup(self.api, self.sandbox_id, max_polling_minutes,
                                             polling_frequency_seconds=30)
        self.update_components()
        sandbox_state = sandbox_details["state"]
        stage = sandbox_details["setup_stage"]
        name = sandbox_details["name"]

        if sandbox_state == SandboxStates.ready_state.value:
            self.setup_finished = True

        # scan activity feed for errors
        if sandbox_state == SandboxStates.error_state.value:
            self.setup_finished = True
            activity_errors = self._get_all_activity_errors(self.sandbox_id)
            if activity_errors:
                # print and store setup error data
                self.setup_errors = activity_errors
                err_msg = f"Error Events during setup:\n{json.dumps(activity_errors, indent=4)}"
                self._print(err_msg)

            if raise_setup_exception:
                err_msg = (f"Sandbox '{name}' Error during SETUP. See events for details.\n"
                           f"Stage: '{stage}'. State '{sandbox_state}'. Sandbox ID: '{self.sandbox_id}'")
                raise SandboxSetupError(err_msg)

        total_minutes = (default_timer() - start) / 60
        self._print(f"Setup finished after {total_minutes:.2f} minutes.")
        return sandbox_details

    def stop_sandbox_and_poll(self, sandbox_id: str, max_polling_minutes=30, raise_teardown_exception=True) -> dict:
        if self.sandbox_ended:
            raise ValueError(f"sandbox {self.sandbox_id} already in completed state")

        last_activity_id = self.api.get_sandbox_activity(self.sandbox_id, tail=1)["events"]["id"]
        start = default_timer()
        self.api.stop_sandbox(sandbox_id)
        sandbox_details = poll_sandbox_teardown(self.api, sandbox_id, max_polling_minutes,
                                                polling_frequency_seconds=30)
        self.update_components()
        sandbox_state = sandbox_details["state"]
        stage = sandbox_details["setup_stage"]
        name = sandbox_details["name"]

        if sandbox_state == SandboxStates.ended_state.value:
            self.sandbox_ended = True

        tail_error_count = 5
        tailed_errors = self.api.get_sandbox_activity(sandbox_id,
                                                      error_only=True,
                                                      from_event_id=last_activity_id + 1,
                                                      tail=tail_error_count)["events"]
        if tailed_errors:
            self.sandbox_ended = True
            self.teardown_errors = tailed_errors
            self._print(f"=== Last {tail_error_count} Errors ===\n{json.dumps(tailed_errors, indent=4)}")

            if raise_teardown_exception:
                err_msg = (f"Sandbox '{name}' Error during SETUP.\n"
                           f"Stage: '{stage}'. State '{sandbox_state}'. Sandbox ID: '{sandbox_id}'")
                raise SandboxTeardownError(err_msg)

        total_minutes = (default_timer() - start) / 60
        self._print(f"Teardown done in {total_minutes:.2f} minutes.")
        return sandbox_details

    def rerun_setup(self):
        pass

    def run_sandbox_command_and_poll(self):
        pass

    def run_component_command_and_poll(self):
        pass

    def _get_all_activity_errors(self, sandbox_id):
        return self.api.get_sandbox_activity(sandbox_id, error_only=True)["events"]

    def publish_sandbox_id_to_env_vars(self):
        """ publish sandbox id as environment variable for different CI process to pick up """
        pass


if __name__ == "__main__":
    api = SandboxRestApiSession("localhost", "admin", "admin")
    controller = SandboxRestController(api)
    response = controller.start_sandbox_and_poll("rest test", "lolol")
    print(json.dumps(response, indent=4))
