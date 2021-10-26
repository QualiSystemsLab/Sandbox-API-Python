import time

import pytest
from env_settings import *

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


@pytest.fixture(scope="session")
def admin_session() -> SandboxRestApiSession:
    with SandboxRestApiSession(CLOUDSHELL_SERVER, CLOUDSHELL_ADMIN_USER, CLOUDSHELL_ADMIN_PASSWORD) as api:
        yield api
        time.sleep(2)
        print("admin session token revoked")
