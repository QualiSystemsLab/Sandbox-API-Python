"""
Test re-running setup to validate blueprint level commands, getting details, and then ending setup execution
"""
import time

import pytest
from common import *
from constants import *

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


@pytest.fixture(scope="module")
def sandbox_id(admin_session: SandboxRestApiSession, empty_blueprint):
    # start sandbox
    start_res = admin_session.start_sandbox(blueprint_id=empty_blueprint, sandbox_name="Pytest empty blueprint test")
    sandbox_id = start_res["id"]
    print(f"Sandbox started: {sandbox_id}")
    yield sandbox_id
    admin_session.stop_sandbox(sandbox_id)
    print(f"\nSandbox ended: {sandbox_id}")


@pytest.fixture(scope="module")
def setup_execution_id(admin_session: SandboxRestApiSession, sandbox_id: str):
    polling_minutes = 2
    counter = 0
    while True:
        if counter > polling_minutes:
            raise Exception("Timeout waiting for setup to end")
        state = admin_session.get_sandbox_details(sandbox_id)["state"]
        if state == "Ready":
            break
        time.sleep(60)
        counter += 1

    print("Rerunning Setup...")
    res = admin_session.run_sandbox_command(sandbox_id=sandbox_id, command_name=BLUEPRINT_SETUP_COMMAND)
    assert isinstance(res, dict)
    print("Setup re-run execution response")
    pretty_print_response(res)
    execution_id = res["executionId"]
    return execution_id


def test_cancel_setup(admin_session, setup_execution_id):
    print("Setup Execution Details")
    res = admin_session.get_execution_details(setup_execution_id)
    pretty_print_response(res)
    print("Ending setup execution")
    admin_session.delete_execution(setup_execution_id)
    print("Setup execution cancelled")
