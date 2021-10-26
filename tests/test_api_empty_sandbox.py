"""
Test the api methods that require a live sandbox against default
- start sandbox
"""
import pytest
from env_settings import DEFAULT_BLUEPRINT_TEMPLATE

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


@pytest.fixture(scope="module")
def sandbox_id(admin_session: SandboxRestApiSession):
    # start sandbox
    start_res = admin_session.start_sandbox(
        blueprint_id=DEFAULT_BLUEPRINT_TEMPLATE, sandbox_name="Pytest empty blueprint test"
    )
    sandbox_id = start_res["id"]
    print(f"Sandbox started: {sandbox_id}")
    yield sandbox_id
    admin_session.stop_sandbox(sandbox_id)
    print(f"\nSandbox ended: {sandbox_id}")


def test_start_stop(admin_session, sandbox_id):
    pass


def test_get_sandbox_details(admin_session, sandbox_id):
    details_res = admin_session.get_sandbox_details(sandbox_id)
    sb_name = details_res["name"]
    print(f"Pulled details for sandbox '{sb_name}'")


def test_get_components(admin_session, sandbox_id):
    sb_components = admin_session.get_sandbox_components(sandbox_id)
    component_count = len(sb_components)
    print(f"component count found: {component_count}")


def test_get_sandbox_commands(admin_session, sandbox_id):
    sb_commands = admin_session.get_sandbox_commands(sandbox_id)
    print(f"Sandbox commands: {[x['name'] for x in sb_commands]}")
    first_sb_command = admin_session.get_sandbox_command_details(sandbox_id, sb_commands[0]["name"])
    print(f"SB command name: {first_sb_command['name']}\n" f"description: {first_sb_command['description']}")


def test_get_sandbox_events(admin_session, sandbox_id):
    activity = admin_session.get_sandbox_activity(sandbox_id)
    events = activity["events"]
    print(f"activity events count: {len(events)}")


def test_get_console_output(admin_session, sandbox_id):
    sb_output = admin_session.get_sandbox_output(sandbox_id)
    entries = sb_output["entries"]
    print(f"Sandbox output entries count: {len(entries)}")


def test_get_instructions(admin_session, sandbox_id):
    instructions = admin_session.get_sandbox_instructions(sandbox_id)
    print(f"Pulled sandbox instructions: '{instructions}'")


def test_extend_sandbox(admin_session, sandbox_id):
    extend_response = admin_session.extend_sandbox(sandbox_id, "PT0H10M")
    print(f"extended sandbox. Remaining time: {extend_response['remaining_time']}")
