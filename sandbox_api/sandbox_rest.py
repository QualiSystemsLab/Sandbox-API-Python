import json
from typing import List

import requests
from dataclasses import dataclass, asdict


class SandboxRestException(Exception):
    pass


@dataclass
class InputParam:
    name: str
    value: str


class SandboxRestApiClient:
    """ Python wrapper for CloudShell Sandbox API """

    def __init__(self, host: str, username: str, password: str, domain='Global', port=82, is_https=False,
                 api_version="v2"):
        """ logs into api and sets headers for future requests """
        protocol = "https" if is_https else "http"
        self._base_url = f"{protocol}://{host}:{port}/api"
        self._versioned_url = f"{self._base_url}/{api_version}"
        self._session = requests.Session()
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
        # sandbox name will default to blueprint name if not passed
        if not sandbox_name:
            sandbox_name = self.get_blueprint_details(blueprint_id)['name']

        data_dict = {"duration": duration, "name": sandbox_name}
        if permitted_users:
            data_dict['permitted_users'] = permitted_users
        if bp_params:
            data_dict["params"] = [asdict(x) for x in bp_params]

        response = requests.post(f'{self._versioned_url}/blueprints/{blueprint_id}/start',
                                 headers=self._auth_headers,
                                 data=json.dumps(data_dict))
        if not response.ok:
            err_msg = self._format_err(response, f"Failed to start sandbox from blueprint{blueprint_id}")
            raise SandboxRestException(err_msg)
        return response.json()

    def start_persistent_sandbox(self, blueprint_id: str, sandbox_name="", bp_params: List[InputParam] = None,
                                 permitted_users: List[str] = None):
        """ Create a persistent sandbox from the provided blueprint id """

        # sandbox name will default to blueprint name if not passed
        if not sandbox_name:
            sandbox_name = self.get_blueprint_details(blueprint_id)['name']

        data_dict = {"name": sandbox_name}
        if permitted_users:
            data_dict['permitted_users'] = permitted_users
        if bp_params:
            data_dict["params"] = [asdict(x) for x in bp_params]

        response = requests.post(f'{self._versioned_url}/blueprints/{blueprint_id}/start-persistent',
                                 headers=self._auth_headers,
                                 data=json.dumps(data_dict))
        if not response.ok:
            err_msg = self._format_err(response, f"Failed to start persistent sandbox from blueprint{blueprint_id}")
            raise SandboxRestException(err_msg)
        return response.json()

    def start_sandbox_command(self, sandbox_id: str, command_name: str, params: List[InputParam] = None,
                              print_output=True):
        """ Run a sandbox level command """
        url = f'{self._versioned_url}/sandboxes/{sandbox_id}/commands/{command_name}/start'
        data_dict = {"printOutput": print_output}
        params = [asdict(x) for x in params] if params else []
        data_dict["params"] = params
        response = requests.post(url, data=json.dumps(data_dict),headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"failed to start sandbox command {command_name}"))
        return response.json()

    def start_component_command(self, sandbox_id: str, component_id: str, command_name: str,
                                params: List[InputParam] = None, print_output: bool = True):
        """ Start a command on sandbox component """
        url = f'{self._versioned_url}/sandboxes/{sandbox_id}/components/{component_id}/commands/{command_name}/start'
        data_dict = {"printOutput": print_output}
        params = [asdict(x) for x in params] if params else []
        data_dict["params"] = params
        response = requests.post(url, data=json.dumps(data_dict),headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"failed to start component command {command_name}"))
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
            raise SandboxRestException(self._format_err(response, f"failed to extend sandbox {sandbox_id}"))
        return response.json()

    def stop_sandbox(self, sandbox_id: str):
        """ Stop the sandbox given sandbox id """
        response = requests.post(f'{self._versioned_url}/sandboxes/{sandbox_id}/stop', headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"Failed to stop sandbox '{sandbox_id}'"))
        return response.json()

    # SANDBOX GET REQUESTS
    def get_sandboxes(self):
        """Get list of sandboxes
        :return:
        """
        response = requests.get(f'{self._versioned_url}/sandboxes', headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"Failed to get sandbox list"))
        return response.json()

    def get_sandbox_details(self, sandbox_id: str):
        """ Get details of the given sandbox id """
        response = requests.get(f'{self._versioned_url}/sandboxes/{sandbox_id}', headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"Failed to get sandbox details for {sandbox_id}"))
        return response.json()

    def get_sandbox_activity(self, sandbox_id: str):
        """ Get list of sandbox activity """
        response = requests.get(f'{self._versioned_url}/sandboxes/{sandbox_id}/activity', headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"Failed to get sandbox activity for {sandbox_id}"))
        return response.json()

    def get_sandbox_commands(self, sandbox_id: str):
        """ Get list of sandbox commands """
        response = requests.get(f'{self._versioned_url}/sandboxes/{sandbox_id}/commands', headers=self._auth_headers)
        if not response.ok:
            raise SandboxRestException(self._format_err(response, f"Failed to get sandbox commands for {sandbox_id}"))
        return response.json()

    def get_sandbox_command_details(self, sandbox_id: str, command_name: str):
        """ Get details of specific sandbox command """
        response = requests.get('{}/v2/sandboxes/{}/commands/{}'.format(
            self._base_url, sandbox_id, command_name),
            headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_components(self, sandbox_id):
        """Get list of sandbox components
        :param str sandbox_id: Sandbox id
        :return: Returns a list of tuples of component type, name and id
        """
        response = requests.get('{}/v2/sandboxes/{}/components'.format(
            self._base_url, sandbox_id), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_component_details(self, sandbox_id, component_id):
        """Get details of components in sandbox
        :param str sandbox_id: Sandbox id
        :param str component_id: Component id
        :return: Returns a tuple of component type, name, id, address, description
        """
        response = requests.get('{}/v2/sandboxes/{}/components/{}'.format(self._base_url, sandbox_id, component_id),
                                headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_component_commands(self, sandbox_id, component_id):
        """Get list of commands for a particular component in sandbox
        :param str sandbox_id: Sandbox id
        :param str component_id: Component id
        :return:
        """
        response = requests.get('{}/v2/sandboxes/{}/components/{}/commands'.format(
            self._base_url, sandbox_id, component_id), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_component_command_details(self, sandbox_id, component_id, command):
        """Get details of a command of sandbox component
        :param str sandbox_id: Sandbox id
        :param str component_id: Component id
        :param str command: Command name
        :return:
        """
        response = requests.get('{}/v2/sandboxes/{}/components/{}/commands/{}'.format(
            self._base_url, sandbox_id, component_id, command), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_output(self, sandbox_id):
        """Get list of sandbox output
        :param str sandbox_id: Sandbox id
        :return:
        """
        response = requests.get('{}/v2/sandboxes/{}/{}'.format(self._base_url, sandbox_id, 'output'),
                                headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

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
        response = requests.get(f'{self._versioned_url}/blueprints/{blueprint_id}')
        if not response.ok:
            raise SandboxRestException(
                self._format_err(response, f"Failed to get blueprint data for {blueprint_id}"))
        return response.json()


usage = """
    bp_name = 'Environment1'
    bp_id = '9a3ad040-14ff-4078-9b0a-6ce7986daaaa'
    sb_duration = 'PT10M'

    sb_cmd = 'blueprint_power_cycle'
    sb_cmd_params = {"params": [{"name": "WaitTime", "value": "1"}], "printOutput": True}
    sb_component = 'Demo Resource 1'
    sb_component_cmd = 'Hello'
    sb_comp_cmd_params = {"params": [{"name": "Duration", "value": "Sandbox tester"}], "printOutput": True}

    sandbox_api = SandboxAPI('localhost', 'admin', 'admin', 'Global')
    r = sandbox_api.get_blueprints()
    print(r)
    r = sandbox_api.get_blueprint_details(bp_name)
    print(r)
    r = sandbox_api.get_blueprint_details(bp_id)
    print(r)
    r = sandbox_api.start_sandbox(bp_name, sb_duration)
    print(r)
    sb_id = r['id']
    r = sandbox_api.get_sandboxes()
    print(r)
    r = sandbox_api.get_sandbox_details(sb_id)
    print(r)
    r = sandbox_api.get_sandbox_commands(sb_id)
    print(r)
    r = sandbox_api.get_sandbox_command_details(sb_id, 'Setup')
    print(r)
    r = sandbox_api.sandbox_command_start(sb_id, sb_cmd, sb_cmd_params)
    print(r)
    r = sandbox_api.get_sandbox_components(sb_id)
    print(r)
    comp_id = [c.get('id') for c in r if c.get('name') == sb_component][0]

    r = sandbox_api.get_sandbox_component_details(sb_id, comp_id)
    print(r)
    r = sandbox_api.get_sandbox_component_commands(sb_id, comp_id)
    print(r)
    r = sandbox_api.get_sandbox_component_command_details(sb_id, comp_id, sb_component_cmd)
    print(r)
    r = sandbox_api.sandbox_component_command_start(
        sb_id, comp_id, sb_component_cmd,
        params=sb_comp_cmd_params)
    print(r)
    r = sandbox_api.extend_sandbox(sb_id, sb_duration)
    print(r)
    r = sandbox_api.get_sandbox_activity(sb_id)
    print(r)
    r = sandbox_api.get_sandbox_output(sb_id)
    print(r)
    print(sandbox_api.stop_sandbox(sb_id))
"""


def main():
    bp_name = 'Environment1'
    bp_id = '9a3ad040-14ff-4078-9b0a-6ce7986daaaa'
    sb_duration = 'PT10M'

    sb_cmd = 'blueprint_power_cycle'
    sb_cmd_params = {"params": [{"name": "WaitTime", "value": "1"}], "printOutput": True}
    sb_component = 'Demo Resource 1'
    sb_component_cmd = 'Hello'
    sb_comp_cmd_params = {"params": [{"name": "Duration", "value": "Sandbox tester"}], "printOutput": True}

    sandbox_api = SandboxRestApiClient('localhost', 'admin', 'admin', 'Global')
    r = sandbox_api.get_blueprints()
    print(r)
    r = sandbox_api.get_blueprint_details(bp_name)
    print(r)
    r = sandbox_api.get_blueprint_details(bp_id)
    print(r)
    r = sandbox_api.start_sandbox(bp_name, sb_duration)
    print(r)
    sb_id = r['id']
    r = sandbox_api.get_sandboxes()
    print(r)
    r = sandbox_api.get_sandbox_details(sb_id)
    print(r)
    r = sandbox_api.get_sandbox_commands(sb_id)
    print(r)
    r = sandbox_api.get_sandbox_command_details(sb_id, 'Setup')
    print(r)
    r = sandbox_api.sandbox_command_start(sb_id, sb_cmd, sb_cmd_params)
    print(r)
    r = sandbox_api.get_sandbox_components(sb_id)
    print(r)
    comp_id = [c.get('id') for c in r if c.get('name') == sb_component][0]

    r = sandbox_api.get_sandbox_component_details(sb_id, comp_id)
    print(r)
    r = sandbox_api.get_sandbox_component_commands(sb_id, comp_id)
    print(r)
    r = sandbox_api.get_sandbox_component_command_details(sb_id, comp_id, sb_component_cmd)
    print(r)
    r = sandbox_api.sandbox_component_command_start(
        sb_id, comp_id, sb_component_cmd,
        params=sb_comp_cmd_params)
    print(r)
    r = sandbox_api.extend_sandbox(sb_id, sb_duration)
    print(r)
    r = sandbox_api.get_sandbox_activity(sb_id)
    print(r)
    r = sandbox_api.get_sandbox_output(sb_id)
    print(r)
    print(sandbox_api.stop_sandbox(sb_id))


if __name__ == '__main__':
    # print(usage)
    # main()
    api = SandboxRestApiClient("localhost", "admin", "admin")
    bps = api.get_blueprints()
    pass
