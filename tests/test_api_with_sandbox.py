"""
Test the api methods that require a live sandbox against default
- start sandbox
"""
from common import DEFAULT_BLUEPRINT_TEMPLATE
from common_fixtures import admin_session

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


def test_simple_flow(admin_session: SandboxRestApiSession):
    """ """
    # start sandbox
    start_res = admin_session.start_sandbox(blueprint_id=DEFAULT_BLUEPRINT_TEMPLATE, sandbox_name="Pytest simple flow")
    sandbox_id = start_res["id"]
    assert sandbox_id
    print(f"Sandbox started. ID: {sandbox_id}")

    # get sandbox details
    details_res = admin_session.get_sandbox_details(sandbox_id)
    sb_name = details_res["name"]
    print(f"Pulled details for sandbox '{sb_name}'")

    # get components - should be empty
    sb_components = admin_session.get_sandbox_components(sandbox_id)
    component_count = len(sb_components)
    print(f"component count found: {component_count}")

    # get activity events

    # get commands

    #
