"""
Test the api methods against blueprint with a resource containing a command.

- Putshell mock can be used - https://community.quali.com/repos/3318/put-shell-mock
- DUT model / command can be referenced in constants.py (Putshell / health_check)
- Assumed that only one DUT is in blueprint
"""
import logging

import common
import constants
import pytest

from cloudshell.sandbox_rest import model
from cloudshell.sandbox_rest.api import SandboxRestApiSession
from timeit import default_timer


@pytest.fixture(scope="module")
def sandbox_id(admin_session: SandboxRestApiSession, sleep_orch_blueprint):
    # start sandbox
    start = default_timer()
    start_res = admin_session.start_sandbox(blueprint_id=sleep_orch_blueprint,
                                            sandbox_name="Pytest POLLING blueprint test",
                                            polling_setup=True,
                                            max_polling_minutes=5,
                                            polling_frequency_seconds=10,
                                            polling_log_level=logging.INFO)
    sandbox_id = start_res.id
    print(f"Sandbox started after {default_timer() - start:.2f} seconds. Sandbox id: {sandbox_id}. State: {start_res.state}")
    yield sandbox_id
    common.fixed_sleep()

    print("cleaning up sandbox")
    # stop sandbox
    stop_timer = default_timer()
    stop_res = admin_session.stop_sandbox(sandbox_id,
                                          poll_teardown=True,
                                          max_polling_minutes=5,
                                          polling_frequency_seconds=10,
                                          polling_log_level=logging.INFO)
    print(f"\nSandbox ended after {default_timer() - stop_timer:.2f} seconds. ID: {sandbox_id}. State: {stop_res.state}")


@pytest.fixture(scope="module")
def component_id(admin_session: SandboxRestApiSession, sandbox_id: str):
    components = admin_session.get_sandbox_components(sandbox_id)
    common.fixed_sleep()
    component_filter = [x for x in components if x.component_type == constants.DUT_MODEL]
    assert component_filter
    return component_filter[0].id


def test_start_stop(sandbox_id):
    print(f"\nstart stop test got sandbox id '{sandbox_id}'")
    assert sandbox_id


def test_component_command_blocking(admin_session: SandboxRestApiSession, sandbox_id: str, component_id: str):
    print("\nStarting blocking DUT Command...")
    start = default_timer()
    response = admin_session.run_component_command(sandbox_id=sandbox_id,
                                                   component_id=component_id,
                                                   command_name=constants.DUT_COMMAND,
                                                   polling_execution=True,
                                                   polling_log_level=logging.INFO)
    common.fixed_sleep()
    assert isinstance(response, model.ResourceCommandExecutionDetails)
    print(f"Resource command finished after {default_timer() - start:.2f} seconds.\n"
          f"Execution response: {response.pretty_json()}")
