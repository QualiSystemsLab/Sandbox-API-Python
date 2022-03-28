import json
import logging
from dataclasses import asdict, dataclass
from typing import List

from abstract_http_client.http_clients.requests_client import RequestsClient

from cloudshell.sandbox_rest.exceptions import SandboxRestAuthException, SandboxRestException
from cloudshell.sandbox_rest import model


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
    Python wrapper for CloudShell Sandbox API
    View http://<API_SERVER>/api/v2/explore to see schemas of return json values
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
        show_insecure_warning=False,
    ):
        """ Login to api and store headers for future requests """
        super().__init__(host, username, password, token, logger, port, use_https, ssl_verify, proxies, show_insecure_warning)
        self._base_uri = "/api"
        self._v2_base_uri = f"{self._base_uri}/v2"
        self.domain = domain
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
            raise SandboxRestAuthException(f"Invalid token. Token response {response.text}")

        return login_token

    def _set_auth_header_on_session(self):
        self.rest_service.session.headers.update({"Authorization": f"Basic {self.token}"})

    def _remove_auth_header_from_session(self):
        self.rest_service.session.headers.pop("Authorization")

    def _validate_auth_header(self) -> None:
        if not self.rest_service.session.headers.get("Authorization"):
            raise SandboxRestAuthException("No Authorization header currently set for session")

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

    # SANDBOX POST REQUESTS
    def start_sandbox(
        self,
        blueprint_id: str,
        sandbox_name="",
        duration="PT2H0M",
        bp_params: List[CommandInputParam] = None,
        permitted_users: List[str] = None,
    ) -> model.SandboxDetails:
        """
        Create a sandbox from the provided blueprint id
        Duration format must be a valid 'ISO 8601'. (e.g 'PT23H' or 'PT4H2M')
        """
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/blueprints/{blueprint_id}/start"
        sandbox_name = sandbox_name if sandbox_name else self.get_blueprint_details(blueprint_id)["name"]

        data = {
            "duration": duration,
            "name": sandbox_name,
            "permitted_users": permitted_users if permitted_users else [],
            "params": [asdict(x) for x in bp_params] if bp_params else [],
        }

        response_dict = self.rest_service.request_post(uri, data).json()
        return model.dict_to_model(response_dict, model.SandboxDetails)

    def start_persistent_sandbox(
        self,
        blueprint_id: str,
        sandbox_name="",
        bp_params: List[CommandInputParam] = None,
        permitted_users: List[str] = None,
    ) -> model.SandboxDetails:
        """ Create a persistent sandbox from the provided blueprint id """
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/blueprints/{blueprint_id}/start-persistent"

        sandbox_name = sandbox_name if sandbox_name else self.get_blueprint_details(blueprint_id)["name"]
        data = {
            "name": sandbox_name,
            "permitted_users": permitted_users if permitted_users else [],
            "params": [asdict(x) for x in bp_params] if bp_params else [],
        }

        response_dict = self.rest_service.request_post(uri, data).json()
        return model.dict_to_model(response_dict, model.SandboxDetails)


    def run_sandbox_command(
        self,
        sandbox_id: str,
        command_name: str,
        params: List[CommandInputParam] = None,
        print_output=True,
    ) -> model.CommandStartResponse:
        """Run a sandbox level command"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/commands/{command_name}/start"
        data = {"printOutput": print_output}
        params = [asdict(x) for x in params] if params else []
        data["params"] = params
        response_dict = self.rest_service.request_post(uri, data).json()
        return model.dict_to_model(response_dict, model.CommandStartResponse)

    def run_component_command(
        self,
        sandbox_id: str,
        component_id: str,
        command_name: str,
        params: List[CommandInputParam] = None,
        print_output: bool = True,
    ) -> model.CommandStartResponse:
        """Start a command on sandbox component"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/components/{component_id}/commands/{command_name}/start"
        data = {"printOutput": print_output}
        params = [asdict(x) for x in params] if params else []
        data["params"] = params
        response_dict = self.rest_service.request_post(uri, data).json()
        return model.dict_to_model(response_dict, model.CommandStartResponse)

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
        return model.dict_to_model(response_dict, model.ExtendResponse)

    def stop_sandbox(self, sandbox_id: str) -> model.StopSandboxResponse:
        """Stop the sandbox given sandbox id"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/stop"
        response_dict = self.rest_service.request_post(uri).json()
        return model.dict_to_model(response_dict, model.StopSandboxResponse)

    # SANDBOX GET REQUESTS
    def get_sandboxes(self, show_historic=False) -> List[model.SandboxDescriptionShort]:
        """Get list of sandboxes"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes"
        params = {"show_historic": "true" if show_historic else "false"}
        response_list = self.rest_service.request_get(uri, params=params).json()
        return model.list_to_model(response_list, model.SandboxDescriptionShort)

    def get_sandbox_details(self, sandbox_id: str) -> model.SandboxDetails:
        """Get details of the given sandbox id"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}"
        response_dict = self.rest_service.request_get(uri).json()
        return model.dict_to_model(response_dict, model.SandboxDetails)

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
            params["error_only"] = error_only
        if since:
            params["since"] = since
        if from_event_id:
            params["from_event_id"] = from_event_id
        if tail:
            params["tail"] = tail

        response_dict = self.rest_service.request_get(uri, params=params).json()
        return model.dict_to_model(response_dict, model.ActivityEventsResponse)

    def get_sandbox_commands(self, sandbox_id: str) -> List[model.Command]:
        """Get list of sandbox commands"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/commands"
        response_list = self.rest_service.request_get(uri).json()
        return model.list_to_model(response_list, model.Command)

    def get_sandbox_command_details(self, sandbox_id: str, command_name: str) -> model.Command:
        """Get details of specific sandbox command"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/commands/{command_name}"
        response_dict = self.rest_service.request_get(uri).json()
        return model.dict_to_model(response_dict, model.Command)

    def get_sandbox_components(self, sandbox_id: str) -> List[model.SandboxComponentFull]:
        """Get list of sandbox components"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/components"
        response_list = self.rest_service.request_get(uri).json()
        return model.list_to_model(response_list, model.SandboxComponentFull)

    def get_sandbox_component_details(self, sandbox_id: str, component_id: str) -> model.SandboxComponentFull:
        """Get details of components in sandbox"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/components/{component_id}"
        response_dict = self.rest_service.request_get(uri).json()
        return model.dict_to_model(response_dict, model.SandboxComponentFull)


    def get_sandbox_component_commands(self, sandbox_id: str, component_id: str) -> List[model.Command]:
        """Get list of commands for a particular component in sandbox"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/components/{component_id}/commands"
        response_list = self.rest_service.request_get(uri).json()
        return model.list_to_model(response_list, model.Command)

    def get_sandbox_component_command_details(self, sandbox_id: str, component_id: str, command: str) -> model.CommandExecutionDetails:
        """Get details of a command of sandbox component"""
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/components/{component_id}/commands/{command}"
        response_dict = self.rest_service.request_get(uri).json()
        return model.dict_to_model(response_dict, model.CommandExecutionDetails)

    def get_sandbox_instructions(self, sandbox_id: str) -> str:
        """ Pull the instructions text of sandbox """
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/sandboxes/{sandbox_id}/instructions"
        return self.rest_service.request_get(uri).json()

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
        return model.dict_to_model(response_dict, model.SandboxOutput)

    # BLUEPRINT GET REQUESTS
    def get_blueprints(self, raw_json=False) -> List[model.BlueprintDescription]:
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/blueprints"
        blueprints_list = self.rest_service.request_get(uri).json()
        return model.list_to_model(blueprints_list, model.BlueprintDescription)

    def get_blueprint_details(self, blueprint_id: str) -> model.BlueprintDescription:
        """
        Get details of a specific blueprint
        Can pass either blueprint name OR blueprint ID
        """
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/blueprints/{blueprint_id}"
        details_dict = self.rest_service.request_get(uri).json()
        return model.dict_to_model(details_dict, model.BlueprintDescription)


    # EXECUTIONS
    def get_execution_details(self, execution_id: str) -> model.CommandExecutionDetails:
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/executions/{execution_id}"
        details_dict = self.rest_service.request_get(uri).json()
        return model.dict_to_model(details_dict, model.CommandExecutionDetails)

    def delete_execution(self, execution_id: str) -> None:
        """
        API returns dict with single key on successful deletion of execution
        {"result": "success"}
        """
        self._validate_auth_header()
        uri = f"{self._v2_base_uri}/executions/{execution_id}"
        response_dict = self.rest_service.request_delete(uri).json()
        if not response_dict["result"] == "success":
            raise SandboxRestException(
                f"Failed execution deletion of id {execution_id}\n" f"{json.dumps(response_dict, indent=4)}"
            )
