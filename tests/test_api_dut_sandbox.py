"""
Test the api methods against blueprint with a resource containing a command.

- Putshell mock can be used - https://community.quali.com/repos/3318/put-shell-mock
- DUT model / command can be referenced in constants.py (Putshell / health_check)
- Assumed that only one DUT is in blueprint
"""
import common
import constants
import pytest

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


@pytest.fixture(scope="module")
def blueprint_id(admin_session: SandboxRestApiSession, dut_blueprint):
    res_id = common.get_blueprint_id_from_name(admin_session, dut_blueprint)
    assert isinstance(res_id, str)
    return res_id


@pytest.fixture(scope="module")
def sandbox_id(admin_session: SandboxRestApiSession, blueprint_id):
    # start sandbox
    start_res = admin_session.start_sandbox(blueprint_id=blueprint_id, sandbox_name="Pytest DUT blueprint test")
    sandbox_id = start_res["id"]
    print(f"Sandbox started: {sandbox_id}")
    common.fixed_sleep()
    yield sandbox_id
    admin_session.stop_sandbox(sandbox_id)
    print(f"\nSandbox ended: {sandbox_id}")


@pytest.fixture(scope="module")
def component_id(admin_session: SandboxRestApiSession, sandbox_id: str):
    components = admin_session.get_sandbox_components(sandbox_id)
    common.fixed_sleep()
    component_filter = [x for x in components if x["component_type"] == constants.DUT_MODEL]
    assert component_filter
    return component_filter[0]["id"]


@pytest.fixture(scope="module")
def execution_id(admin_session: SandboxRestApiSession, sandbox_id: str, component_id: str):
    print("Starting DUT Command...")
    res = admin_session.run_component_command(
        sandbox_id=sandbox_id, component_id=component_id, command_name=constants.DUT_COMMAND
    )
    common.fixed_sleep()
    assert isinstance(res, dict)
    print("Started execution response")
    common.pretty_print_response(res)
    execution_id = res["executionId"]
    return execution_id


@pytest.fixture(scope="module")
def test_get_execution_details(admin_session, execution_id):
    res = admin_session.get_execution_details(execution_id)
    common.fixed_sleep()
    assert isinstance(res, dict)
    return res


def test_delete_execution(admin_session, execution_id, test_get_execution_details):
    print("Execution Details")
    common.pretty_print_response(test_get_execution_details)
    is_supports_cancellation = test_get_execution_details["supports_cancellation"]
    if not is_supports_cancellation:
        print("Can't cancel this command. Returning")
        return
    print("Stopping execution...")
    admin_session.delete_execution(execution_id)
    common.fixed_sleep()
    print("Execution deleted")
