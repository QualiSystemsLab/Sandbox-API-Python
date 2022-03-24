import time

import pytest
from constants import *
from env_settings import *

from cloudshell.sandbox_rest.api import SandboxRestApiSession


@pytest.fixture(scope="session")
def admin_session() -> SandboxRestApiSession:
    admin_api = SandboxRestApiSession(
        host=CLOUDSHELL_SERVER, username=CLOUDSHELL_ADMIN_USER, password=CLOUDSHELL_ADMIN_PASSWORD, domain=CLOUDSHELL_DOMAIN
    )
    print(f"Admin session started. Token: {admin_api.token}")
    with admin_api:
        yield admin_api
        time.sleep(3)

    print("admin session token revoked")
    print(f"total requests: {admin_api.rest_service.request_counter}")


@pytest.fixture(scope="session")
def empty_blueprint():
    return DEFAULT_EMPTY_BLUEPRINT


@pytest.fixture(scope="session")
def dut_blueprint():
    return DUT_BLUEPRINT
