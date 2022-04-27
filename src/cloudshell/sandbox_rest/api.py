"""
Module that handles the Sandbox Rest API session
Handles login and wraps all api methods
Returns Pydantic BaseModel responses of returned JSON
"""
import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Callable, List

from abstract_http_client.http_clients.requests_client import RequestsClient
from tenacity import RetryError, retry, retry_if_result, stop_after_delay, wait_fixed

from cloudshell.sandbox_rest import exceptions, model
from pydantic.main import ValidationError


@dataclass
class CommandInputParam:
    """
    param objects passed to sandbox / component command endpoints
    sandbox global inputs, commands and resource commands all follow this generic name/value convention
    """

    name: str
    value: str


class SandboxRestApiSession(RequestsClient):
    """
    Python client for CloudShell Sandbox REST api
    View swagger UI at http://<API_SERVER>/api/v2/explore for raw JSON response schema
    """

    def __init__(
            self,
            host: str,
            username="",
            password="",
            domain="Global",
            token="",
            port=82,
            logger: logging.Logger = None,
            use_https=False,
            ssl_verify=False,
            proxies: dict = None,
            show_insecure_warning=False
    ):
        """ Login to api and store headers for future requests """
        self.logger = logger
        super().__init__(host, username, password, token, logger, port, use_https, ssl_verify, proxies, show_insecure_warning)
        self.domain = domain
        self._base_uri = "/api"
        self._v2_base_uri = f"{self._base_uri}/v2"
        self.login()

    def login(self, user="", password="", token="", domain="") -> None:
        """ Called from init - can also be used to refresh session with credentials """
        self.user = user or self.user
        self.password = password or self.password
        self.token = token or self.token
        self.domain = domain or self.domain

        if not self.domain:
            raise ValueError("Domain must be passed to login")

        if not self.token:
            if not self.user or not self.password:
                raise ValueError("Login requires Token or Username / Password")
            self.token = self._get_token_with_credentials(self.user, self.password, self.domain)

        self._set_auth_header_on_session()

    def logout(self) -> None:
        if not self.token:
            return
        self.delete_token(self.token)
        self.token = None
        self._remove_auth_header_from_session()

    def _get_token_with_credentials(self, user_name: str, password: str, domain: str) -> str:
        """
        Get token from credentials - extraneous quotes stripped off token string
        """
        uri = f"{self._base_uri}/login"
        data = {"username": user_name, "password": password, "domain": domain}
        response = self.rest_service.request_put(uri, data)

        login_token = response.text[1:-1]
        if not login_token:
            err_msg = f"Invalid token. Token response {response.text}"
            raise exceptions.SandboxRestAuthException(err_msg)

        return login_token

    def _set_auth_header_on_session(self):
        self.rest_service.session.headers.update({"Authorization": f"Basic {self.token}"})

    def _remove_auth_header_from_session(self):
        self.rest_service.session.headers.pop("Authorization")

    def _validate_auth_header(self) -> None:
        if not self.rest_service.session.headers.get("Authorization"):
            raise exceptions.SandboxRestAuthException("No Authorization header currently set for session")

    def get_token_for_target_user(self, user_name: str) -> str:
        """
        Get token for target user - remove extraneous quotes
        """
        self._validate_auth_header()
        uri = f"{self._base_uri}/token"
        data = {"username": user_name}
        response = self.rest_service.request_post(uri, data)
        login_token = response.text[1:-1]
        return login_token

    def delete_token(self, token_id: str) -> None:
        self._validate_auth_header()
        uri = f"{self._base_uri}/token/{token_id}"
        return self.rest_service.request_delete(uri).text

    # BLUEPRINT GET REQUESTS
    def get_blueprints(self) -> List[model.BlueprintDescription]:
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/blueprints"
        blueprints_list = self.rest_service.request_get(uri).json()
        return model.BlueprintDescription.list_to_models(blueprints_list)

    def get_blueprint_details(self, blueprint_id: str) -> model.BlueprintDescription:
        """
        Get details of a specific blueprint
        Can pass either blueprint name OR blueprint ID
        """
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/blueprints/{blueprint_id}"
        details_dict = self.rest_service.request_get(uri).json()
        return model.BlueprintDescription.dict_to_model(details_dict)

    # SANDBOX POST REQUESTS
    def _start_sandbox(
            self,
            blueprint_id: str,
            sandbox_name: str,
            duration: str = None,
            bp_params: List[CommandInputParam] = None,
            permitted_users: List[str] = None,
            polling_setup: bool = False,
            max_polling_minutes: int = 20,
            polling_frequency_seconds: int = 30,
            polling_log_level: int = logging.DEBUG,
    ) -> model.SandboxDetails:
        """ internal implementation request to handle both regular and persistent sandbox requests """
        self._validate_auth_header()
        if duration:
            uri = f"{self._v2_base_uri}/blueprints/{blueprint_id}/start"
        else:
            uri = f"{self._v2_base_uri}/blueprints/{blueprint_id}/start-persistent"

        sandbox_name = sandbox_name if sandbox_name else self.get_blueprint_details(blueprint_id).name

        payload = {
            "name": sandbox_name,
            "permitted_users": permitted_users if permitted_users else [],
            "params": [asdict(x) for x in bp_params] if bp_params else [],
        }
        if duration:
            payload["duration"] = duration

        response_dict = self.rest_service.request_post(uri, payload).json()
        sandbox_details = model.SandboxDetails.dict_to_model(response_dict)
        if polling_setup:
            return self.poll_sandbox_setup(
                sandbox_details.id, max_polling_minutes, polling_frequency_seconds, polling_log_level
            )

        return sandbox_details

    def start_sandbox(
            self,
            blueprint_id: str,
            sandbox_name: str = "",
            duration: str = "PT2H0M",
            bp_params: List[CommandInputParam] = None,
            permitted_users: List[str] = None,
            polling_setup: bool = False,
            max_polling_minutes: int = 20,
            polling_frequency_seconds: int = 30,
            polling_log_level: int = logging.DEBUG,
    ) -> model.SandboxDetails:
        """
        Create a sandbox from the provided blueprint id
        Duration format must be a valid 'ISO 8601'. (e.g 'PT23H' or 'PT4H2M')
        """
        return self._start_sandbox(
            blueprint_id=blueprint_id,
            sandbox_name=sandbox_name,
            duration=duration,
            bp_params=bp_params,
            permitted_users=permitted_users,
            polling_setup=polling_setup,
            max_polling_minutes=max_polling_minutes,
            polling_frequency_seconds=polling_frequency_seconds,
            polling_log_level=polling_log_level
        )

    def start_persistent_sandbox(
            self,
            blueprint_id: str,
            sandbox_name: str = "",
            bp_params: List[CommandInputParam] = None,
            permitted_users: List[str] = None,
            polling_setup: bool = False,
            max_polling_minutes: int = 20,
            polling_frequency_seconds: int = 30,
            polling_log_level: int = logging.DEBUG,
    ) -> model.SandboxDetails:
        """
        Create a PERSISTENT sandbox from the provided blueprint id
        Duration format must be a valid 'ISO 8601'. (e.g 'PT23H' or 'PT4H2M')
        """
        return self._start_sandbox(
            blueprint_id=blueprint_id,
            sandbox_name=sandbox_name,
            duration=None,
            bp_params=bp_params,
            permitted_users=permitted_users,
            polling_setup=polling_setup,
            max_polling_minutes=max_polling_minutes,
            polling_frequency_seconds=polling_frequency_seconds,
            polling_log_level=polling_log_level
        )

    def run_sandbox_command(
            self,
            sandbox_id: str,
            command_name: str,
            params: List[CommandInputParam] = None,
            print_output=True,
            polling_execution: bool = False,
            max_polling_minutes: int = 20,
            polling_frequency_seconds: int = 10,
            polling_log_level: int = logging.DEBUG
    ) -> model.SandboxCommandExecutionDetails:
        """Run a sandbox level command"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/commands/{command_name}/start"
        data = {"printOutput": print_output}
        params = [asdict(x) for x in params] if params else []
        data["params"] = params
        response_dict = self.rest_service.request_post(uri, data).json()
        start_response = model.CommandStartResponse.dict_to_model(response_dict)
        model_wrapped_command_params = [model.CommandParameterNameValue(x.name, x.value) for x in params] if params else []
        command_context = model.SandboxCommandContext(sandbox_id=sandbox_id,
                                                      command_name=command_name,
                                                      command_params=model_wrapped_command_params)
        if polling_execution:
            execution_details = self.poll_command_execution(execution_id=start_response.executionId,
                                                            max_polling_minutes=max_polling_minutes,
                                                            polling_frequency_seconds=polling_frequency_seconds,
                                                            log_level=polling_log_level)
        else:
            execution_details = self.get_execution_details(start_response.executionId)

        return model.SandboxCommandExecutionDetails(id=start_response.executionId,
                                                    status=execution_details.status,
                                                    supports_cancellation=execution_details.supports_cancellation,
                                                    started=execution_details.started,
                                                    ended=execution_details.ended,
                                                    output=execution_details.output,
                                                    command_context=command_context)

    def run_component_command(
            self,
            sandbox_id: str,
            component_id: str,
            command_name: str,
            params: List[CommandInputParam] = None,
            print_output: bool = True,
            polling_execution: bool = False,
            max_polling_minutes: int = 20,
            polling_frequency_seconds: int = 10,
            polling_log_level: int = logging.DEBUG
    ) -> model.ComponentCommandExecutionDetails:
        """Start a command on sandbox component"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/components/{component_id}/commands/{command_name}/start"
        data = {"printOutput": print_output}
        params_dicts = [asdict(x) for x in params] if params else []
        data["params"] = params_dicts
        response_dict = self.rest_service.request_post(uri, data).json()
        start_response = model.CommandStartResponse.dict_to_model(response_dict)
        component_details = self.get_sandbox_component_details(sandbox_id, component_id)
        model_wrapped_command_params = [model.CommandParameterNameValue(x.name, x.value) for x in params] if params else []
        command_context = model.ComponentCommandContext(sandbox_id=sandbox_id,
                                                        command_name=command_name,
                                                        command_params=model_wrapped_command_params,
                                                        component_name=component_details.name,
                                                        component_id=component_details.id)
        if polling_execution:
            execution_details = self.poll_command_execution(execution_id=start_response.executionId,
                                                            max_polling_minutes=max_polling_minutes,
                                                            polling_frequency_seconds=polling_frequency_seconds,
                                                            log_level=polling_log_level)
        else:
            execution_details = self.get_execution_details(start_response.executionId)

        return model.ComponentCommandExecutionDetails(id=start_response.executionId,
                                                      status=execution_details.status,
                                                      supports_cancellation=execution_details.supports_cancellation,
                                                      started=execution_details.started,
                                                      ended=execution_details.ended,
                                                      output=execution_details.output,
                                                      command_context=command_context)

    def extend_sandbox(self, sandbox_id: str, duration: str) -> model.ExtendResponse:
        """Extend the sandbox
        :param str sandbox_id: Sandbox id
        :param str duration: duration in ISO 8601 format (P1Y1M1DT1H1M1S = 1year, 1month, 1day, 1hour, 1min, 1sec)
        :return:
        """
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/extend"
        data = {"extended_time": duration}
        response_dict = self.rest_service.request_post(uri, data).json()
        return model.ExtendResponse.dict_to_model(response_dict)

    def stop_sandbox(
            self,
            sandbox_id: str,
            poll_teardown=False,
            max_polling_minutes: int = 20,
            polling_frequency_seconds: int = 30,
            polling_log_level: str = logging.DEBUG,
    ) -> model.SandboxDetails:
        """Stop the sandbox given sandbox id"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/stop"
        response_dict = self.rest_service.request_post(uri).json()

        stop_response = model.StopSandboxResponse.dict_to_model(response_dict)
        if "success" not in stop_response.result:
            raise exceptions.TeardownFailedException(f"Failed to stop sandbox. result:\n{json.dumps(response_dict)}")

        if poll_teardown:
            return self.poll_sandbox_teardown(sandbox_id, max_polling_minutes, polling_frequency_seconds, polling_log_level)

        # if not polling, give teardown request chance to propagate before getting status
        time.sleep(3)
        return self.get_sandbox_details(sandbox_id)

    # SANDBOX GET REQUESTS
    def get_sandboxes(self, show_historic=False) -> List[model.SandboxDescriptionShort]:
        """Get list of sandboxes"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes"
        params = {"show_historic": "true" if show_historic else "false"}
        response_list = self.rest_service.request_get(uri, params=params).json()
        return model.SandboxDescriptionShort.list_to_models(response_list)

    def get_sandbox_details(self, sandbox_id: str) -> model.SandboxDetails:
        """Get details of the given sandbox id"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}"
        response_dict = self.rest_service.request_get(uri).json()
        return model.SandboxDetails.dict_to_model(response_dict)

    def get_sandbox_activity(
            self,
            sandbox_id: str,
            error_only=False,
            since="",
            from_event_id: int = None,
            tail: int = None,
    ) -> model.ActivityEventsResponse:
        """
        Get list of sandbox activity
        'since' - format must be a valid 'ISO 8601'. (e.g 'PT23H' or 'PT4H2M')
        'from_event_id' - integer id of event where to start pulling results from
        'tail' - how many of the last entries you want to pull
        'error_only' - to filter for error events only
        """
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/activity"
        params = {}

        if error_only:
            params["error_only"] = "true"
        if since:
            params["since"] = since
        if from_event_id:
            params["from_event_id"] = from_event_id
        if tail:
            params["tail"] = tail

        response_dict = self.rest_service.request_get(uri, params=params).json()
        return model.ActivityEventsResponse.dict_to_model(response_dict)

    def get_sandbox_commands(self, sandbox_id: str) -> List[model.Command]:
        """Get list of sandbox commands"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/commands"
        response_list = self.rest_service.request_get(uri).json()
        return model.Command.list_to_models(response_list)

    def get_sandbox_command_details(self, sandbox_id: str, command_name: str) -> model.Command:
        """Get details of specific sandbox command"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/commands/{command_name}"
        response_dict = self.rest_service.request_get(uri).json()
        return model.Command.dict_to_model(response_dict)

    def get_sandbox_components(self, sandbox_id: str) -> List[model.SandboxComponentFull]:
        """Get list of sandbox components"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/components"
        response_list = self.rest_service.request_get(uri).json()
        return model.SandboxComponentFull.list_to_models(response_list)

    def get_sandbox_component_details(self, sandbox_id: str, component_id: str) -> model.SandboxComponentFull:
        """Get details of components in sandbox"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/components/{component_id}"
        response_dict = self.rest_service.request_get(uri).json()
        return model.SandboxComponentFull.dict_to_model(response_dict)

    def get_sandbox_component_commands(self, sandbox_id: str, component_id: str) -> List[model.Command]:
        """Get list of commands for a particular component in sandbox"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/components/{component_id}/commands"
        response_list = self.rest_service.request_get(uri).json()
        return model.Command.list_to_models(response_list)

    def get_sandbox_component_command_details(
            self, sandbox_id: str, component_id: str, command: str
    ) -> model.CommandExecutionDetails:
        """Get details of a command of sandbox component"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/components/{component_id}/commands/{command}"
        response_dict = self.rest_service.request_get(uri).json()
        return model.CommandExecutionDetails.dict_to_model(response_dict)

    def get_sandbox_instructions(self, sandbox_id: str) -> str:
        """ Pull the instructions text of sandbox """
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/instructions"
        return self.rest_service.request_get(uri).text

    def get_sandbox_output(
            self,
            sandbox_id: str,
            tail: int = None,
            from_entry_id: int = None,
            since: str = None,
    ) -> model.SandboxOutput:
        """Get list of sandbox output"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/output"
        params = {}
        if tail:
            params["tail"] = tail
        if from_entry_id:
            params["from_entry_id"] = from_entry_id
        if since:
            params["since"] = since

        response_dict = self.rest_service.request_get(uri, params=params).json()
        return model.SandboxOutput.dict_to_model(response_dict)

    # EXECUTIONS
    def get_execution_details(self, execution_id: str) -> model.CommandExecutionDetails:
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/executions/{execution_id}"
        details_dict = self.rest_service.request_get(uri).json()
        try:
            execution_details = model.CommandExecutionDetails.dict_to_model(details_dict)
        except ValidationError as e:
            err_msg = f"Validation error on execution '{execution_id}. Raw JSON:\n{json.dumps(details_dict, indent=4)}"
            if self.logger:
                self.logger.error(err_msg)
            raise
        return execution_details

    def delete_execution(self, execution_id: str) -> dict:
        """
        API returns dict with single key on successful deletion of execution
        {"result": "success"}
        """
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/executions/{execution_id}"
        response_dict = self.rest_service.request_delete(uri).json()
        if not response_dict["result"] == "success":
            raise exceptions.SandboxRestException(
                f"Failed execution deletion of id {execution_id}\n" f"{json.dumps(response_dict, indent=4)}"
            )
        return response_dict

    # Polling
    def _poll_orchestration_state(
            self,
            orchestration_type: str,
            reservation_id: str,
            polling_func: Callable,
            max_polling_minutes: int,
            polling_frequency_seconds: int,
            log_level=logging.DEBUG,
    ) -> model.SandboxDetails:
        """ Create blocking polling process """

        def poll_and_log(sb_details: model.SandboxDetails):
            if self.logger:
                polling_msg = f"Polling {orchestration_type} for sandbox '{sb_details.id}'. State: {sb_details.state}..."
                self.logger.log(log_level, polling_msg)
            return polling_func(sb_details)

        @retry(
            retry=retry_if_result(poll_and_log),
            wait=wait_fixed(polling_frequency_seconds),
            stop=stop_after_delay(max_polling_minutes * 60),
        )
        def retry_poll_sandbox_details():
            return self.get_sandbox_details(reservation_id)

        try:
            sandbox_details = retry_poll_sandbox_details()
        except RetryError:
            raise exceptions.OrchestrationPollingTimeout(f"Sandbox Polling timed out after {max_polling_minutes} minutes")
        return sandbox_details

    def poll_sandbox_setup(
            self, reservation_id: str, max_polling_minutes=20, polling_frequency_seconds=30, log_level: int = logging.DEBUG
    ) -> model.SandboxDetails:
        """ poll setup until completion """
        sandbox_details = self._poll_orchestration_state(
            orchestration_type="SETUP",
            reservation_id=reservation_id,
            polling_func=_should_keep_polling_setup,
            max_polling_minutes=max_polling_minutes,
            polling_frequency_seconds=polling_frequency_seconds,
            log_level=log_level,
        )
        setup_state = sandbox_details.state
        sandbox_id = sandbox_details.id
        if setup_state == model.SandboxStates.ERROR:
            error_activity = self.get_sandbox_activity(sandbox_id, error_only=True)
            raise exceptions.SetupFailedException(
                f"Sandbox setup failed - sandbox id: '{sandbox_id}'", error_events=error_activity.events
            )
        return sandbox_details

    def poll_sandbox_teardown(
            self, reservation_id: str, max_polling_minutes=20, polling_frequency_seconds=30, log_level: int = logging.DEBUG
    ) -> model.SandboxDetails:
        """ poll teardown until completion  """
        latest_event_request = self.get_sandbox_activity(reservation_id, tail=1).events
        latest_event_id = latest_event_request[0].id if latest_event_request else 0
        sandbox_details = self._poll_orchestration_state(
            orchestration_type="TEARDOWN",
            reservation_id=reservation_id,
            polling_func=_should_keep_polling_teardown,
            max_polling_minutes=max_polling_minutes,
            polling_frequency_seconds=polling_frequency_seconds,
            log_level=log_level,
        )
        teardown_error_events = self.get_sandbox_activity(
            reservation_id, error_only=True, from_event_id=latest_event_id
        ).events
        if teardown_error_events:
            raise exceptions.TeardownFailedException(
                f"Failed teardown - sandbox id: '{reservation_id}'", error_events=teardown_error_events
            )
        return sandbox_details

    def poll_command_execution(self,
                               execution_id: str,
                               max_polling_minutes=10,
                               polling_frequency_seconds=30,
                               log_level=logging.DEBUG,
                               ) -> model.CommandExecutionDetails:
        """ Create blocking polling process """

        def poll_and_log(execution_data: model.CommandExecutionDetails) -> bool:
            if self.logger:
                polling_msg = f"Polling execution '{execution_data.id}'.  Status: '{execution_data.status}'..."
                self.logger.log(log_level, polling_msg)
            return _should_keep_polling_execution(execution_data)

        @retry(
            retry=retry_if_result(poll_and_log),
            wait=wait_fixed(polling_frequency_seconds),
            stop=stop_after_delay(max_polling_minutes * 60),
        )
        def retry_poll_execution():
            return self.get_execution_details(execution_id)

        pre_poll_execution_details = self.get_execution_details(execution_id)
        try:
            execution_details = retry_poll_execution()
        except RetryError:
            err_msg = f"Execution '{pre_poll_execution_details.id}' timed out after {max_polling_minutes} minutes"
            raise exceptions.CommandPollingTimeout(err_msg)
        return execution_details


# Polling Helpers
def _should_keep_polling_setup(sandbox_details: model.SandboxDetails) -> bool:
    """ if still in setup keep polling """
    post_setup_states = model.SandboxStates.get_post_setup_states()
    if sandbox_details.state not in post_setup_states:
        return True
    return False


def _should_keep_polling_teardown(sandbox_details: model.SandboxDetails) -> bool:
    """ if in teardown keep polling """
    if sandbox_details.state == model.SandboxStates.TEARDOWN:
        return True
    return False


def _should_keep_polling_execution(execution_data: model.CommandExecutionDetails) -> bool:
    unfinished_states = model.CommandExecutionStates.get_incomplete_execution_states()
    if execution_data.status in unfinished_states:
        return True
    return False
