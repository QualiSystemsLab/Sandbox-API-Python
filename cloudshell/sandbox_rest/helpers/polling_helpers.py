"""
Helper functions to poll the state of sandbox setup or the execution status of a command.
Using 'retrying' library to do polling:
https://pypi.org/project/retrying/
"""
from typing import List, Callable
from retrying import retry  # pip install retrying
from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiClient
from enum import Enum


class SandboxStates(Enum):
    before_setup_state = "BeforeSetup"
    running_setup_state = "Setup"
    error_state = "Error"
    ready_state = "Ready"
    teardown_state = "Teardown"
    ended_state = "Ended"


class ExecutionStatuses(Enum):
    running_status = "Running"
    pending_status = "Pending"
    completed_status = "Completed"
    failed_status = "Failed"


UNFINISHED_EXECUTION_STATUSES = [ExecutionStatuses.running_status.value,
                                 ExecutionStatuses.pending_status.value]


def _should_we_keep_polling_setup(sandbox_details: dict) -> bool:
    """ if still in setup keep polling """
    setup_states = [SandboxStates.before_setup_state.value, SandboxStates.running_setup_state.value]
    if sandbox_details["state"] in setup_states:
        return True
    return False


def _should_we_keep_polling_teardown(sandbox_details: dict) -> bool:
    """ if in teardown keep polling """
    if sandbox_details["state"] == SandboxStates.teardown_state.value:
        return True
    return False


def _poll_sandbox_state(api: SandboxRestApiClient, reservation_id: str, polling_func: Callable,
                        max_polling_minutes: int, polling_frequency_seconds: int) -> str:
    """ Create blocking polling process """

    # retry wait times are in milliseconds
    @retry(retry_on_result=polling_func, wait_fixed=polling_frequency_seconds * 1000,
           stop_max_delay=max_polling_minutes * 60000)
    def get_sandbox_details():
        return api.get_sandbox_details(reservation_id)

    return get_sandbox_details()


def poll_sandbox_setup(api: SandboxRestApiClient, reservation_id: str, max_polling_minutes=20,
                       polling_frequency_seconds=30) -> dict:
    """ poll until completion """
    sandbox_details = _poll_sandbox_state(api, reservation_id, _should_we_keep_polling_setup, max_polling_minutes,
                                          polling_frequency_seconds)
    return sandbox_details


def poll_sandbox_teardown(api: SandboxRestApiClient, reservation_id: str, max_polling_minutes=20,
                          polling_frequency_seconds=30) -> dict:
    """ poll until completion  """
    sandbox_details = _poll_sandbox_state(api, reservation_id, _should_we_keep_polling_teardown, max_polling_minutes,
                                          polling_frequency_seconds)
    return sandbox_details


def _should_we_keep_polling_execution(exc_data: dict) -> bool:
    current_exc_status = exc_data["status"]
    if current_exc_status in UNFINISHED_EXECUTION_STATUSES:
        return True
    return False


def poll_execution_for_completion(sandbox_rest: SandboxRestApiClient, command_execution_id: str,
                                  max_polling_in_minutes=20, polling_frequency_in_seconds=30) -> str:
    """
    poll execution for "Completed" status, then return the execution output
    """
    # retry wait times are in milliseconds
    @retry(retry_on_result=_should_we_keep_polling_execution, wait_fixed=polling_frequency_in_seconds * 1000,
           stop_max_delay=max_polling_in_minutes * 60000)
    def get_execution_data():
        exc_data = sandbox_rest.get_execution_details(command_execution_id)
        return exc_data
    return get_execution_data(sandbox_rest, command_execution_id)


