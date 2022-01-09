"""
Test the api methods that do NOT require a blueprint
Live Cloudshell server is still a dependency
"""
import common
import pytest
from constants import DEFAULT_EMPTY_BLUEPRINT

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


@pytest.fixture(scope="module")
def api_token(admin_session: SandboxRestApiSession):
    token = admin_session.get_token_for_target_user("admin")
    return token


def test_delete_token(admin_session: SandboxRestApiSession, api_token: str):
    assert isinstance(api_token, str)
    print(f"Token response: '{api_token}'")
    admin_session.delete_token(api_token)


def test_get_sandboxes(admin_session: SandboxRestApiSession):
    res = admin_session.get_sandboxes()
    common.random_sleep()
    assert isinstance(res, list)
    print(f"Sandbox count found in system: {len(res)}")


def test_get_blueprints(admin_session: SandboxRestApiSession):
    bp_res = admin_session.get_blueprints()
    common.random_sleep()
    assert isinstance(bp_res, list)
    print(f"Blueprint count found in system: '{len(bp_res)}'")


def test_get_default_blueprint(admin_session: SandboxRestApiSession):
    bp_res = admin_session.get_blueprint_details(DEFAULT_EMPTY_BLUEPRINT)
    common.random_sleep()
    assert isinstance(bp_res, dict)
    bp_name = bp_res["name"]
    print(f"Pulled details for '{bp_name}'")
