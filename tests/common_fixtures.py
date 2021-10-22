import pytest

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


@pytest.fixture
def dut_bp_name() -> str:
    """ For testing basic operations """
    return "DUT Test"


@pytest.fixture
def dut_resource_name() -> str:
    """ For testing basic operations """
    return "DUT_1"


@pytest.fixture
def admin_session() -> SandboxRestApiSession:
    return SandboxRestApiSession("localhost", "admin", "admin")
