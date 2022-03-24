"""
Helper functions to poll the state of sandbox setup or the execution status of a command.
Using 'tenacity' library to do polling:
https://github.com/jd/tenacity
"""
import asyncio
import logging
from enum import Enum
from time import sleep
from typing import Callable, List

from tenacity import RetryError, retry, retry_if_result, stop_after_delay, wait_fixed  # pip install tenacity

import cloudshell.sandbox_rest.exceptions as exceptions
from cloudshell.sandbox_rest.api import SandboxRestApiSession


class SandboxStates(Enum):
    BEFORE_SETUP = "BeforeSetup"
    RUNNING_SETUP = "Setup"
    ERROR = "Error"
    READY = "Ready"
    TEARDOWN = "Teardown"
    ENDED = "Ended"


class ExecutionStatuses(Enum):
    RUNNING = "Running"
    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"


SANDBOX_SETUP_STATES = [SandboxStates.BEFORE_SETUP.value, SandboxStates.RUNNING_SETUP.value]
SANDBOX_ACTIVE_STATES = [SandboxStates.READY.value, SandboxStates.ERROR.value]
UNFINISHED_EXECUTION_STATUSES = [ExecutionStatuses.RUNNING.value, ExecutionStatuses.PENDING.value]


def _should_keep_polling_setup(sandbox_details: dict) -> bool:
    """ if still in setup keep polling """
    setup_states = [SandboxStates.BEFORE_SETUP.value, SandboxStates.RUNNING_SETUP.value]
    if sandbox_details["state"] in setup_states:
        return True
    return False


def _should_keep_polling_teardown(sandbox_details: dict) -> bool:
    """ if in teardown keep polling """
    if sandbox_details["state"] == SandboxStates.TEARDOWN.value:
        return True
    return False


def _should_keep_polling_execution(exc_data: dict) -> bool:
    current_exc_status = exc_data["status"]
    if current_exc_status in UNFINISHED_EXECUTION_STATUSES:
        return True
    return False


def log_orchestration_polling(orchestration_type: str, sandbox_id: str, logger: logging.Logger = None):
    if logger:
        polling_msg = f"Polling {orchestration_type} for sandbox '{sandbox_id}'..."
        logger.info(polling_msg)


def _poll_orchestration_state(
    orchestration_type: str,
    api: SandboxRestApiSession,
    reservation_id: str,
    polling_func: Callable,
    max_polling_minutes: int,
    polling_frequency_seconds: int,
    logger: logging.Logger = None,
) -> str:
    """ Create blocking polling process """

    # retry wait times are in milliseconds
    @retry(
        retry=retry_if_result(polling_func),
        wait=wait_fixed(polling_frequency_seconds * 1000),
        stop=stop_after_delay(max_polling_minutes * 60000),
        before=log_orchestration_polling(orchestration_type, reservation_id, logger),
    )
    def get_sandbox_details():
        return api.get_sandbox_details(reservation_id)

    try:
        sandbox_details = get_sandbox_details()
    except RetryError:
        raise exceptions.OrchestrationPollingTimeout(
            f"Sandbox Polling timed out after configured {max_polling_minutes} minutes"
        )
    return sandbox_details


def poll_sandbox_setup(
    api: SandboxRestApiSession,
    reservation_id: str,
    max_polling_minutes=20,
    polling_frequency_seconds=30,
    logger: logging.Logger = None,
) -> dict:
    """ poll until completion """
    sandbox_details = _poll_orchestration_state(
        "Setup", api, reservation_id, _should_keep_polling_setup, max_polling_minutes, polling_frequency_seconds, logger
    )
    setup_state = sandbox_details["state"]
    sandbox_id = sandbox_details["id"]
    if setup_state == SandboxStates.ERROR.value:
        raise exceptions.SetupFailedException(f"Sandbox setup failed for sandbox '{sandbox_id}'")
    return sandbox_details


def poll_sandbox_teardown(
    api: SandboxRestApiSession,
    reservation_id: str,
    max_polling_minutes=20,
    polling_frequency_seconds=30,
    logger: logging.Logger = None,
) -> dict:
    """ poll until completion  """
    sandbox_details = _poll_orchestration_state(
        "Teardown", api, reservation_id, _should_keep_polling_teardown, max_polling_minutes, polling_frequency_seconds, logger
    )
    return sandbox_details


def poll_execution(
    sandbox_rest: SandboxRestApiSession, command_execution_id: str, max_polling_in_minutes=20, polling_frequency_in_seconds=30
) -> str:
    """
    poll execution for "Completed" status, then return the execution output
    """

    @retry(
        retry=retry_if_result(_should_keep_polling_execution),
        wait=wait_fixed(polling_frequency_in_seconds),
        stop=stop_after_delay(max_polling_in_minutes * 60),
    )
    def get_execution_response():
        response = sandbox_rest.get_execution_details(command_execution_id)
        return response

    try:
        execution_response = get_execution_response(sandbox_rest, command_execution_id)
    except RetryError:
        raise exceptions.CommandPollingTimeout(f"Execution polling timed out after max {max_polling_in_minutes} minutes")
    execution_status = execution_response["status"]
    execution_id = execution_response["id"]
    if execution_status == ExecutionStatuses.FAILED.value:
        raise exceptions.CommandExecutionFailed(f"Execution '{execution_id}' ended with failed result")
    return execution_response["output"]
