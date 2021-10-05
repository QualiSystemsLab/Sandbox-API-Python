import pytest
from cloudshell_test.sandbox_rest.sandbox_api import SandboxRestApiClient
from datetime import datetime
import json
from dataclasses import dataclass

DEFAULT_BLUEPRINT_TEMPLATE = "CloudShell Sandbox Template"
DUT_RESOURCE = "DUT_1"
HEALTH_CHECK_COMMAND = "health_check"


@dataclass
class SandboxTestData:
    blueprint_name: str
    sandbox_command: str


@dataclass
class ResourceTestData:
    resource_name: str
    resource_command: str


@pytest.fixture(name="dut_bp")
def dut_blueprint_fixture():
    """ For testing basic operations """
    return "DUT Test"


@pytest.fixture(name="session")
def rest_session_fixture():
    return SandboxRestApiClient("localhost", "admin", "admin")


def _pretty_print_response(dict_response):
    json_str = json.dumps(dict_response, indent=4)
    print(f"\n{json_str}")


class TestNoBlueprint:
    def test_get_sandboxes(self, session: SandboxRestApiClient):
        res = session.get_sandboxes()
        _pretty_print_response(res)


class TestEmptyBlueprint:
    bp_data = SandboxTestData(blueprint_name=DEFAULT_BLUEPRINT_TEMPLATE, sandbox_command="Setup")

    def test_simple_flow(self, session: SandboxRestApiClient):
        start_response = session.start_sandbox(self.bp_data.blueprint_name, f"test sandbox - {datetime.now()}")
        print(f"\nblueprint {start_response['name']} started")
