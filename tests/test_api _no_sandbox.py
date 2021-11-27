"""
Test the api methods that do NOT require a blueprint
Live Cloudshell server is still a dependency
"""
from constants import DEFAULT_EMPTY_BLUEPRINT

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


def test_get_sandboxes(admin_session: SandboxRestApiSession):
    res = admin_session.get_sandboxes()
    assert type(res) is list
    print(f"Sandbox count found in system: {len(res)}")


def test_get_blueprints(admin_session: SandboxRestApiSession):
    bp_res = admin_session.get_blueprints()
    assert type(bp_res) is list
    print(f"Blueprint count found in system: '{len(bp_res)}'")


def test_get_default_blueprint(admin_session: SandboxRestApiSession):
    bp_res = admin_session.get_blueprint_details(DEFAULT_EMPTY_BLUEPRINT)
    assert type(bp_res) is dict
    bp_name = bp_res["name"]
    print(f"Pulled details for '{bp_name}'")


def test_get_and_delete_token(admin_session: SandboxRestApiSession):
    """ get token for admin user """
    token_res = admin_session.get_token_for_target_user("admin")
    assert type(token_res) is str
    print(f"Token response: '{token_res}'")
