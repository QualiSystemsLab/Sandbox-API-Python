"""
Test the api methods that do NOT require a blueprint
Live Cloudshell server is still a dependency
"""
import common
import constants
import env_settings
import pytest

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


@pytest.fixture(scope="module")
def api_token(admin_session: SandboxRestApiSession):
    token = admin_session.get_token_for_target_user("admin")
    print(f"Get User token response: '{token}'")
    return token


def test_login_with_token(api_token):
    new_api = SandboxRestApiSession(host=env_settings.CLOUDSHELL_SERVER, token=api_token)
    print(f"\nnew api token: {new_api.token}")
    sandbox_res = new_api.get_sandboxes()
    assert isinstance(sandbox_res, list)
    new_api.delete_token(new_api.token)
    print("new api token deleted")


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
    bp_res = admin_session.get_blueprint_details(constants.DEFAULT_EMPTY_BLUEPRINT)
    common.random_sleep()
    assert isinstance(bp_res, dict)
    bp_name = bp_res["name"]
    print(f"Pulled details for '{bp_name}'")
