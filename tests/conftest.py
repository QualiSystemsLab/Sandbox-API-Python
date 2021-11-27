import time

import pytest
from constants import *
from env_settings import *

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


@pytest.fixture(scope="session")
def admin_session() -> SandboxRestApiSession:
    with SandboxRestApiSession(
        host=CLOUDSHELL_SERVER,
        username=CLOUDSHELL_ADMIN_USER,
        password=CLOUDSHELL_ADMIN_PASSWORD,
        domain=CLOUDSHELL_DOMAIN,
    ) as api:
        yield api
        time.sleep(2)
        print("admin session token revoked")


@pytest.fixture(scope="session")
def empty_blueprint():
    return DEFAULT_EMPTY_BLUEPRINT


@pytest.fixture(scope="session")
def dut_blueprint():
    return DUT_BLUEPRINT
