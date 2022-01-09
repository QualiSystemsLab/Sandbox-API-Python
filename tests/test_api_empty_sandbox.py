"""
Test the api methods that require an empty, PUBLIC blueprint
"""

import common
import pytest

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


@pytest.fixture(scope="module")
def blueprint_id(admin_session: SandboxRestApiSession, empty_blueprint):
    res_id = common.get_blueprint_id_from_name(admin_session, empty_blueprint)
    assert isinstance(res_id, str)
    return res_id


@pytest.fixture(scope="module")
def sandbox_id(admin_session: SandboxRestApiSession, blueprint_id):
    # start sandbox
    start_res = admin_session.start_sandbox(blueprint_id=blueprint_id, sandbox_name="Pytest empty blueprint test")
    sandbox_id = start_res["id"]
    print(f"Sandbox started: {sandbox_id}")
    yield sandbox_id
    admin_session.stop_sandbox(sandbox_id)
    print(f"\nSandbox ended: {sandbox_id}")


def test_start_stop(sandbox_id):
    assert isinstance(sandbox_id, str)
    print(f"Sandbox ID: {sandbox_id}")


def test_get_sandbox_details(admin_session, sandbox_id):
    common.random_sleep()
    details_res = admin_session.get_sandbox_details(sandbox_id)
    assert isinstance(details_res, dict)
    sb_name = details_res["name"]
    print(f"Pulled details for sandbox '{sb_name}'")


def test_get_components(admin_session, sandbox_id):
    common.random_sleep()
    components_res = admin_session.get_sandbox_components(sandbox_id)
    assert isinstance(components_res, list)
    component_count = len(components_res)
    print(f"component count found: {component_count}")


def test_get_sandbox_commands(admin_session, sandbox_id):
    common.random_sleep()
    commands_res = admin_session.get_sandbox_commands(sandbox_id)
    assert isinstance(commands_res, list)
    print(f"Sandbox commands: {[x['name'] for x in commands_res]}")
    first_sb_command = admin_session.get_sandbox_command_details(sandbox_id, commands_res[0]["name"])
    print(f"SB command name: {first_sb_command['name']}\n" f"description: {first_sb_command['description']}")


def test_get_sandbox_events(admin_session, sandbox_id):
    common.random_sleep()
    activity_res = admin_session.get_sandbox_activity(sandbox_id)
    assert isinstance(activity_res, dict) and "events" in activity_res
    events = activity_res["events"]
    print(f"activity events count: {len(events)}")


def test_get_console_output(admin_session, sandbox_id):
    common.random_sleep()
    output_res = admin_session.get_sandbox_output(sandbox_id)
    assert isinstance(output_res, dict) and "entries" in output_res
    entries = output_res["entries"]
    print(f"Sandbox output entries count: {len(entries)}")


def test_get_instructions(admin_session, sandbox_id):
    common.random_sleep()
    instructions_res = admin_session.get_sandbox_instructions(sandbox_id)
    assert isinstance(instructions_res, str)
    print(f"Pulled sandbox instructions: '{instructions_res}'")


def test_extend_sandbox(admin_session, sandbox_id):
    common.random_sleep()
    extend_response = admin_session.extend_sandbox(sandbox_id, "PT0H10M")
    assert isinstance(extend_response, dict) and "remaining_time" in extend_response
    print(f"extended sandbox. Remaining time: {extend_response['remaining_time']}")
