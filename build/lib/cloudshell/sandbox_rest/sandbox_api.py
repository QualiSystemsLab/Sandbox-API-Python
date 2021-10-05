import json
from typing import List

import requests
from dataclasses import dataclass, asdict


class SandboxRestException(Exception):
    """ General exception to raise inside Rest client class """
    pass


@dataclass
class InputParam:
    """ To model the param objects passed to sandbox / component command endpoints """
    name: str
    value: str


class SandboxRestApiClient:
    """
    Python wrapper for CloudShell Sandbox API
    View http://<API_SERVER>/api/v2/explore to see schemas of return json values
    """

    def __init__(self, host: str, username: str, password: str, domain='Global', port=82, is_https=False,
                 api_version="v2"):
        """ login to api and store headers for future requests """
        protocol = "https" if is_https else "http"
        self._base_url = f"{protocol}://{host}:{port}/api"
        self._versioned_url = f"{self._base_url}/{api_version}"
        self._auth_headers = self._get_auth_headers(username, password, domain)

    def _get_auth_headers(self, user_name: str, password: str, domain: str):
        """
        Get token from login response, then place token into auth headers on class
        """
        login_res = requests.put(url=f"{self._base_url}/login",
                                 data=json.dumps({"username": user_name, "password": password, "domain": domain}),
                                 headers={"Content-Type": "application/json"})

        if not login_res.ok:
            raise SandboxRestException(self._format_err(login_res, "Failed Login"))

        login_token = login_res.text[1:-1]

        auth_headers = {
            'Authorization': f'Basic {login_token}',
            'Content-Type': 'application/json'
        }
        return auth_headers

    @staticmethod
    def _format_err(response: requests.Response, custom_err_msg="Failed Api Call"):
        err_msg = f"Response Code: {response.status_code}, Reason: {response.reason}"
        if custom_err_msg:
            err_msg = f"{custom_err_msg}. {err_msg}"
        return err_msg

    # SANDBOX POST REQUESTS
    def start_sandbox(self, blueprint_id: str, sandbox_name="", duration="PT2H0M",
                      bp_params: List[InputParam] = None, permitted_users: List[str] = None):
        """
        Create a sandbox from the provided blueprint id
        Duration format must be a valid 'ISO 8601'. (e.g 'PT23H' or 'PT4H2M')
        """
        url = f'{self._versioned_url}/blueprints/{blueprint_id}/start'
        sandbox_name = sandbox_name if sandbox_name else self.get_blueprint_details(blueprint_id)['name']

        data_dict = {
            "duration": duration,
            "name": sandbox_name,
            "permitted_users": permitted_users if permitted_users else [],
            "params": [asdict(x) for x in bp_params] if bp_params else []
        }

        response = requests.post(url, headers=self._auth_headers, data=json.dumps(data_dict))
        if not response.ok:
            err_msg = self._format_err(response, f"Failed to start sandbox from blueprint '{blueprint_id}'")
            raise SandboxRestException(err_msg)
        return response.json()

    def start_persistent_sandbox(self, blueprint_id: str, sandbox_name="", bp_params: List[InputParam] = None,
                                 permitted_users: List[str] = None):
        """ Create a persistent sandbox from the provided blueprint id """
        url = f'{self._versioned_url}/blueprints/{blueprint_id}/start-persistent'

        sandbox_name = sandbox_name if sandbox_name else self.get_blueprint_details(blueprint_id)['name']
        data_dict = {
            "name": sandbox_name,
            "permitted_users": permitted_users if permitted_users else [],
            "params": [asdict(x) for x in bp_params] if bp_params else []
        }

        response = requests.post(url, headers=self._auth_headers, data=json.dumps(data_dict))
        if not response.ok:
            err_msg = self._format_err(response, f"Failed to start persistent sandbox from blueprint '{blueprint_id}'")
            raise SandboxRestException(err_msg)
        return response.json()

    def run_sandbox_command(self, sandbox_id: str, command_name: str, params: List[InputParam] = None,
                            print_output=True):
        """ Run a sandbox level command """
        url = f'{self._versioned_url}/sandboxes/{sandbox_id}/commands/{command_name}/start'
        data_dict = {"printOutput": print_output}
        params = [asdict(x) for x in params] if params else []
        data_dict["params"] = params
        response = requests.post(url, data=json.dumps(data_dict), headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"failed to start sandbox command '{command_name}'"))
        return response.json()

    def run_component_command(self, sandbox_id: str, component_id: str, command_name: str,
                              params: List[InputParam] = None, print_output: bool = True):
        """ Start a command on sandbox component """
        url = f'{self._versioned_url}/sandboxes/{sandbox_id}/components/{component_id}/commands/{command_name}/start'
        data_dict = {"printOutput": print_output}
        params = [asdict(x) for x in params] if params else []
        data_dict["params"] = params
        response = requests.post(url, data=json.dumps(data_dict), headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(
                self._format_err(response, f"failed to start component command '{command_name}'"))
        return response.json()

    def extend_sandbox(self, sandbox_id: str, duration: str):
        """Extend the sandbox
        :param str sandbox_id: Sandbox id
        :param str duration: duration in ISO 8601 format (P1Y1M1DT1H1M1S = 1year, 1month, 1day, 1hour, 1min, 1sec)
        :return:
        """
        data_dict = {"extended_time": duration}
        response = requests.post(f'{self._base_url}/sandboxes/{sandbox_id}/extend',
                                 data=json.dumps(data_dict),
                                 headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"failed to extend sandbox '{sandbox_id}'"))
        return response.json()

    def stop_sandbox(self, sandbox_id: str):
        """ Stop the sandbox given sandbox id """
        response = requests.post(f'{self._versioned_url}/sandboxes/{sandbox_id}/stop', headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"Failed to stop sandbox '{sandbox_id}'"))
        return response.json()

    # SANDBOX GET REQUESTS
    def get_sandboxes(self, show_historic=False):
        """Get list of sandboxes
        :return:
        """
        params = {"show_historic": show_historic}
        response = requests.get(f'{self._versioned_url}/sandboxes', headers=self._auth_headers, params=params)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"Failed to get sandbox list"))
        return response.json()

    def get_sandbox_details(self, sandbox_id: str):
        """ Get details of the given sandbox id """
        response = requests.get(f'{self._versioned_url}/sandboxes/{sandbox_id}', headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"Failed to get sandbox details for '{sandbox_id}'"))
        return response.json()

    def get_sandbox_activity(self, sandbox_id: str, error_only=False, since="", from_event_id: int = None,
                             tail: int = None):
        """
        Get list of sandbox activity
        'since' - format must be a valid 'ISO 8601'. (e.g 'PT23H' or 'PT4H2M')
        'from_event_id' - integer id of event where to start pulling results from
        'tail' - how many of the last entries you want to pull
        'error_only' - to filter for error events only
        """
        url = f'{self._versioned_url}/sandboxes/{sandbox_id}/activity'
        params = {}

        if error_only:
            params["error_only"] = error_only
        if since:
            params["since"] = since
        if from_event_id:
            params["from_event_id"] = from_event_id
        if tail:
            params["tail"] = tail

        if params:
            response = requests.get(url, headers=self._auth_headers, params=params)
        else:
            response = requests.get(url, headers=self._auth_headers)

        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"Failed to get sandbox activity for '{sandbox_id}'"))
        return response.json()

    def get_sandbox_commands(self, sandbox_id: str):
        """ Get list of sandbox commands """
        response = requests.get(f'{self._versioned_url}/sandboxes/{sandbox_id}/commands', headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"Failed to get sandbox commands for '{sandbox_id}'"))
        return response.json()

    def get_sandbox_command_details(self, sandbox_id: str, command_name: str):
        """ Get details of specific sandbox command """
        response = requests.get(f'{self._versioned_url}/sandboxes/{sandbox_id}/commands/{command_name}',
                                headers=self._auth_headers)
        if not response.ok:
            err_msg = self._format_err(response,
                                       f"Failed to get sandbox command details for '{command_name}' in '{sandbox_id}'")
            raise SandboxRestException(err_msg)
        return response.json()

    def get_sandbox_components(self, sandbox_id: str):
        """ Get list of sandbox components """
        response = requests.get(f'{self._versioned_url}/sandboxes/{sandbox_id}/components', headers=self._auth_headers)
        if not response.ok:
            err_msg = self._format_err(response, f"Failed to get sandbox components details for '{sandbox_id}'")
            raise SandboxRestException(err_msg)
        return response.json()

    def get_sandbox_component_details(self, sandbox_id: str, component_id: str):
        """ Get details of components in sandbox """
        response = requests.get(f'{self._versioned_url}/sandboxes/{sandbox_id}/components/{component_id}',
                                headers=self._auth_headers)
        if not response.ok:
            custom_err_msg = (f"Failed to get sandbox component details for component: '{component_id}', "
                              f"sandbox: '{sandbox_id}'")
            err_msg = self._format_err(response, custom_err_msg)
            raise SandboxRestException(err_msg)
        return response.json()

    def get_sandbox_component_commands(self, sandbox_id: str, component_id: str):
        """ Get list of commands for a particular component in sandbox """
        response = requests.get(f'{self._versioned_url}/sandboxes/{sandbox_id}/components/{component_id}/commands',
                                headers=self._auth_headers)
        if not response.ok:
            custom_err_msg = (f"Failed to get sandbox component commands list for component: '{component_id}', "
                              f"sandbox: '{sandbox_id}'")
            err_msg = self._format_err(response, custom_err_msg)
            raise SandboxRestException(err_msg)
        return response.json()

    def get_sandbox_component_command_details(self, sandbox_id: str, component_id: str, command: str):
        """ Get details of a command of sandbox component """
        response = requests.get(
            f'{self._versioned_url}/sandboxes/{sandbox_id}/components/{component_id}/commands/{command}',
            headers=self._auth_headers)
        if not response.ok:
            custom_err_msg = (f"Failed to get sandbox component command details for component: '{component_id}', "
                              f"sandbox: '{sandbox_id}'")
            err_msg = self._format_err(response, custom_err_msg)
            raise SandboxRestException(err_msg)
        return response.json()

    def get_sandbox_instructions(self, sandbox_id: str):
        """ pull the instruction text of sandbox """
        response = requests.get(f'{self._versioned_url}/sandboxes/{sandbox_id}/instructions',
                                headers=self._auth_headers)
        if not response.ok:
            err_msg = self._format_err(response,
                                       f"Failed to get sandbox instructions for '{sandbox_id}'")
            raise SandboxRestException(err_msg)
        return response.json()

    def get_sandbox_output(self, sandbox_id: str, tail: int = None, from_entry_id: int = None, since: str = None):
        """ Get list of sandbox output """
        url = f'{self._versioned_url}/sandboxes/{sandbox_id}/instructions'
        params = {}
        if tail:
            params["tail"] = tail
        if from_entry_id:
            params["from_entry_id"] = from_entry_id
        if since:
            params["since"] = since

        if params:
            response = requests.get(url, headers=self._auth_headers, params=params)
        else:
            response = requests.get(url, headers=self._auth_headers)

        if not response.ok:
            err_msg = self._format_err(response,
                                       f"Failed to get sandbox instructions for '{sandbox_id}'")
            raise SandboxRestException(err_msg)
        return response.json()

    # BLUEPRINT GET REQUESTS
    def get_blueprints(self):
        """ Get list of blueprints """
        response = requests.get(f'{self._versioned_url}/blueprints', headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, "Failed to get blueprints"))
        return response.json()

    def get_blueprint_details(self, blueprint_id: str):
        """
        Get details of a specific blueprint
        Can pass either blueprint name OR blueprint ID
        """
        response = requests.get(f"{self._versioned_url}/blueprints/'{blueprint_id}'")
        if not response.ok:
            raise SandboxRestException(
                self._format_err(response, f"Failed to get blueprint data for '{blueprint_id}'"))
        return response.json()

    # EXECUTIONS
    def get_execution_details(self, execution_id: str):
        response = requests.get(f"{self._versioned_url}/executions/{execution_id}", headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(
                self._format_err(response, f"Failed to get execution details for '{execution_id}'"))
        return response.json()

    def delete_execution(self, execution_id: str):
        response = requests.delete(f"{self._versioned_url}/executions/{execution_id}", headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(
                self._format_err(response, f"Failed to delete execution for '{execution_id}'"))
        return response.json()


if __name__ == '__main__':
    api = SandboxRestApiClient("localhost", "admin", "admin")
    bps = api.get_blueprints()
    pass
