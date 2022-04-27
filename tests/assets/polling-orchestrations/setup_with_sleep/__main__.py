from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow
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

DefaultSetupWorkflow().register(sandbox)
sandbox.workflow.add_to_configuration(fake_config)
sandbox.execute_setup()
