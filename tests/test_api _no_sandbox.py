"""
Test the api methods that do not require a live sandbox
- get all blueprints
- get all sandboxes
- get blueprint by id
- get token + delete token
"""
from common import DEFAULT_BLUEPRINT_TEMPLATE, pretty_print_response
from common_fixtures import admin_session

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


def test_get_sandboxes(admin_session: SandboxRestApiSession):
    res = admin_session.get_sandboxes()
    print(f"Sandbox count found in system: {len(res)}")


def test_get_blueprints(admin_session: SandboxRestApiSession):
    bp_res = admin_session.get_blueprints()
    print(f"Blueprint count found in system: '{len(bp_res)}'")


def test_get_default_blueprint(admin_session: SandboxRestApiSession):
    bp_res = admin_session.get_blueprint_details(DEFAULT_BLUEPRINT_TEMPLATE)
    bp_name = bp_res["name"]
    print(f"Pulled details for '{bp_name}'")


def test_get_and_delete_token(admin_session: SandboxRestApiSession):
    """ get token for admin user """
    token_res = admin_session.get_token_for_target_user("admin")
    print(f"Token response: '{token_res}'")
    admin_session.delete_token(token_res)
    print("deleted token")
