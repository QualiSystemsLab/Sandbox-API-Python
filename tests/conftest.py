import time

import pytest
import constants
import env_settings

from cloudshell.sandbox_rest.api import SandboxRestApiSession
from cloudshell.sandbox_rest.default_logger import set_up_default_logger


@pytest.fixture(scope="session")
def admin_session() -> SandboxRestApiSession:
    admin_api = SandboxRestApiSession(host=env_settings.CLOUDSHELL_SERVER,
                                      username=env_settings.CLOUDSHELL_ADMIN_USER,
                                      password=env_settings.CLOUDSHELL_ADMIN_PASSWORD,
                                      domain=env_settings.CLOUDSHELL_DOMAIN,
                                      logger=set_up_default_logger())
    print(f"Admin session started. Token: {admin_api.token}")
    with admin_api:
        yield admin_api
        time.sleep(3)

    print("admin session token revoked")
    print(f"total requests: {admin_api.rest_service.request_counter}")


@pytest.fixture(scope="session")
def empty_blueprint():
    return constants.DEFAULT_EMPTY_BLUEPRINT


@pytest.fixture(scope="session")
def dut_blueprint():
    return constants.DUT_BLUEPRINT


@pytest.fixture(scope="session")
def sleep_orch_blueprint():
    return constants.SLEEP_ORCH_BLUEPRINT
