from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.teardown.default_teardown_orchestrator import DefaultTeardownWorkflow
import time

SLEEP_SECONDS = 30


def fake_config(sandbox, components=None):
    """
    pretend to configure but then go to sleep
    :param Sandbox sandbox:
    :param components:
    :return:
    """
    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, f"starting fake config for {SLEEP_SECONDS} seconds")
    time.sleep(SLEEP_SECONDS)


sandbox = Sandbox()

DefaultTeardownWorkflow().register(sandbox)
sandbox.workflow.before_teardown_started(fake_config)

sandbox.execute_teardown()
