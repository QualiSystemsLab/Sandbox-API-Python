"""
Test the api methods that require an empty, PUBLIC blueprint
"""
import time

import pytest
from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession
from constants import *
from common import *


@pytest.fixture(scope="module")
def blueprint_id(admin_session: SandboxRestApiSession, empty_blueprint):
    res_id = get_blueprint_id_from_name(admin_session, empty_blueprint)
    assert(type(res_id) is str)
    return res_id


@pytest.fixture(scope="module")
def sandbox_id(admin_session: SandboxRestApiSession, blueprint_id):
    # start sandbox
    start_res = admin_session.start_sandbox(
        blueprint_id=blueprint_id, sandbox_name="Pytest empty blueprint test"
    )
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
    res = admin_session.run_sandbox_command(sandbox_id=sandbox_id,
                                            command_name=BLUEPRINT_SETUP_COMMAND)
    assert (type(res) is dict)
    print("Setup re-run execution response")
    pretty_print_response(res)
    execution_id = res["executionId"]
    return execution_id


def test_start_stop(admin_session, sandbox_id):
    assert (type(sandbox_id) is str)
    print(f"Sandbox ID: {sandbox_id}")


def test_get_sandbox_details(admin_session, sandbox_id):
    details_res = admin_session.get_sandbox_details(sandbox_id)
    assert (type(details_res) is dict)
    sb_name = details_res["name"]
    print(f"Pulled details for sandbox '{sb_name}'")


def test_get_components(admin_session, sandbox_id):
    components_res = admin_session.get_sandbox_components(sandbox_id)
    assert (type(components_res) is list)
    component_count = len(components_res)
    print(f"component count found: {component_count}")


def test_get_sandbox_commands(admin_session, sandbox_id):
    commands_res = admin_session.get_sandbox_commands(sandbox_id)
    assert (type(commands_res) is list)
    print(f"Sandbox commands: {[x['name'] for x in commands_res]}")
    first_sb_command = admin_session.get_sandbox_command_details(sandbox_id, commands_res[0]["name"])
    print(f"SB command name: {first_sb_command['name']}\n" f"description: {first_sb_command['description']}")


def test_get_sandbox_events(admin_session, sandbox_id):
    activity_res = admin_session.get_sandbox_activity(sandbox_id)
    assert (type(activity_res) is dict and "events" in activity_res)
    events = activity_res["events"]
    print(f"activity events count: {len(events)}")


def test_get_console_output(admin_session, sandbox_id):
    output_res = admin_session.get_sandbox_output(sandbox_id)
    assert (type(output_res) is dict and "entries" in output_res)
    entries = output_res["entries"]
    print(f"Sandbox output entries count: {len(entries)}")


def test_get_instructions(admin_session, sandbox_id):
    instructions_res = admin_session.get_sandbox_instructions(sandbox_id)
    assert (type(instructions_res) is str)
    print(f"Pulled sandbox instructions: '{instructions_res}'")


def test_extend_sandbox(admin_session, sandbox_id):
    extend_response = admin_session.extend_sandbox(sandbox_id, "PT0H10M")
    assert (type(extend_response) is dict and "remaining_time" in extend_response)
    print(f"extended sandbox. Remaining time: {extend_response['remaining_time']}")
