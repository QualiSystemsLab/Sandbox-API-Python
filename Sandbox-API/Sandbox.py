import json
import requests


class SandboxAPI:
    """ Python wrapper for CloudShell Sandbox API
    """
    def __init__(self, host, username, password, domain='Global', port=82):
        """Initializes and logs in Sandbox
        :param str host: hostname of IP address of sandbox API server
        :param str username: CloudShell username
        :param str password: CloudShell password
        :param str domain: CloudShell domain (default=Global)
        :param int port: Sandbox API port number(default=82)
        """
        self._server_url = 'http://{}:{}/api'.format(host, port)
        response = requests.put('{}/login'.format(self._server_url),
                                json={'username': username, 'password': password, 'domain': domain})

        self._headers = {"Authorization": "Basic " + response.content[1:-1].decode('utf-8'),
                         "Content-Type": "application/json"}

    def get_blueprints(self):
        """Get list of blueprints
        :return:
        """
        response = requests.get('{}/v2/blueprints'.format(self._server_url), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_blueprint_details(self, blueprint_id):
        """Get details of a specific blueprint
        :param blueprint_id: Blueprint name or id
        :return:
        """
        response = requests.get('{}/v2/blueprints/{}'.format(self._server_url, blueprint_id), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def start_sandbox(self, blueprint_id, duration, sandbox_name=None, parameters=None, permitted_users=None):
        """Create a sandbox from the provided blueprint id
        :param list permitted_users: list of permitted users ex: ['user1', 'user2']
        :param list parameters: List of dicts, input parameters in the format ex: [{"name": "Version",
            "value": "3.0"}, {"name": "Build Number", "value": "5"}]
        :param str blueprint_id: blueprint_id or name
        :param str duration: duration in ISO 8601 format (P1Y1M1DT1H1M1S = 1year, 1month, 1day, 1hour, 1min, 1sec)
        :param str sandbox_name: name of the sandbox, same as blueprint if name=''
        :return:
        """
        if not sandbox_name:
            sandbox_name = self.get_blueprint_details(blueprint_id)['name']
        data_dict = {"duration": duration, "name": sandbox_name}
        if permitted_users:
            data_dict['permitted_users'] = permitted_users
        if parameters:
            data_dict["params"] = parameters

        response = requests.post('{}/v2/blueprints/{}/start'.format(self._server_url, blueprint_id),
                                 headers=self._headers,
                                 data=json.dumps(data_dict))
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandboxes(self):
        """Get list of sandboxes
        :return:
        """
        response = requests.get('{}/v2/sandboxes'.format(self._server_url), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_details(self, sandbox_id):
        """Get details of the given sandbox id
        :param sandbox_id: Sandbox id
        :return:
        """
        response = requests.get('{}/v2/sandboxes/{}'.format(self._server_url, sandbox_id), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_activity(self, sandbox_id):
        """Get list of sandbox activity
        :param str sandbox_id: Sandbox id
        :return:
        """
        response = requests.get('{}/v2/sandboxes/{}/{}'.format(self._server_url, sandbox_id, 'activity'),
                                headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_commands(self, sandbox_id):
        """Get list of sandbox commands
        :param str sandbox_id: Sandbox id
        :return:
        """
        response = requests.get('{}/v2/sandboxes/{}/commands'.format(self._server_url, sandbox_id),
                                headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_command_details(self, sandbox_id, command_name):
        """Get details of specific sandbox command
        :param str sandbox_id: Sandbox id
        :param str command_name: Sandbox command to be executed
        :return:
        """
        response = requests.get('{}/v2/sandboxes/{}/commands/{}'.format(
            self._server_url, sandbox_id, command_name),
            headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def sandbox_command_start(self, sandbox_id, command_name, params=None):
        """Start a sandbox command
        :param str sandbox_id: Sandbox id
        :param str command_name: Sandbox command to be executed
        :param dict params: parameters to be passed to the command ex: {"params": [{"name": "WaitTime", "value": "1"}],
            "printOutput": True}
        :return:
        """
        if params:
            response = requests.post('{}/v2/sandboxes/{}/commands/{}/start'.format(
                self._server_url, sandbox_id, command_name),
                data=json.dumps(params),
                headers=self._headers)
        else:
            response = requests.post('{}/v2/sandboxes/{}/commands/{}/start'.format(
                self._server_url, sandbox_id, command_name),
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
            self._server_url, sandbox_id), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_component_details(self, sandbox_id, component_id):
        """Get details of components in sandbox
        :param str sandbox_id: Sandbox id
        :param str component_id: Component id
        :return: Returns a tuple of component type, name, id, address, description
        """
        response = requests.get('{}/v2/sandboxes/{}/components/{}'.format(self._server_url, sandbox_id, component_id),
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
            self._server_url, sandbox_id, component_id), headers=self._headers)
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
            self._server_url, sandbox_id, component_id, command), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def sandbox_component_command_start(self, sandbox_id, component_id, command_name, params=None):
        """Start a command on sandbox component
        :param str sandbox_id: Sandbox id
        :param str component_id: Component id
        :param str command_name: Command name
        :param dict params: parameters to be passed to the command ex:
            {"params": [{"name": "Duration", "value": "Sandbox tester"}], "printOutput": True}
        :return:
        """
        if params:
            response = requests.post('{}/v2/sandboxes/{}/components/{}/commands/{}/start'.format(
                self._server_url, sandbox_id, component_id, command_name), data=json.dumps(params),
                headers=self._headers)
        else:
            response = requests.post('{}/v2/sandboxes/{}/components/{}/commands/{}/start'.format(
                self._server_url, sandbox_id, component_id, command_name), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def extend_sandbox(self, sandbox_id, duration):
        """Extend the sandbox
        :param str sandbox_id: Sandbox id
        :param str duration: duration in ISO 8601 format (P1Y1M1DT1H1M1S = 1year, 1month, 1day, 1hour, 1min, 1sec)
        :return:
        """
        data_dict = json.loads('{"extended_time": "' + duration + '"}')
        response = requests.post('{}/v2/sandboxes/{}/extend'.format(self._server_url, sandbox_id),
                                 data=json.dumps(data_dict), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def get_sandbox_output(self, sandbox_id):
        """Get list of sandbox output
        :param str sandbox_id: Sandbox id
        :return:
        """
        response = requests.get('{}/v2/sandboxes/{}/{}'.format(self._server_url, sandbox_id, 'output'),
                                headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason

    def stop_sandbox(self, sandbox_id):
        """Stop the sandbox given sandbox id
        :param sandbox_id: Sandbox id
        :return:
        """
        response = requests.post('{}/v2/sandboxes/{}/stop'.format(self._server_url, sandbox_id), headers=self._headers)
        if response.ok:
            return json.loads(response.content)
        return response.reason


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


if __name__ == '__main__':
    print(usage)
    main()
