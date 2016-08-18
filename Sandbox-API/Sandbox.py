import requests
import json


class Sandbox:
    """
    Sandbox Python API wrapper
    """

    def __init__(self, config_file):
        quali_config = json.load(open(config_file, 'r'))
        self.server_address = 'http://{}:{}/api'.format(quali_config['server_name'], quali_config['server_port'])
        self.username = quali_config['username']
        self.password = quali_config['password']
        self.domain = quali_config['domain']
        self.auth_code = ''
        self.headers = ''

    def _request_and_parse(self, request_type, url_str, json_dict={}, data_dict={}):
        """

        :param request_type:
        :param url_str:
        :param json_dict:
        :param data_dict:
        :return:
        """

        response = ''
        if request_type.lower() == 'put':
            response = requests.put(url_str, json=json_dict, headers=self.headers)

        elif request_type.lower() == 'get':
            response = requests.get(url_str, json=json_dict, headers=self.headers)

        elif request_type.lower() == 'post':
            response = requests.post(url_str, json=json_dict, headers=self.headers, data=json.dumps(data_dict))

        if not response.ok:
            raise Exception('Error code: {}\nError text: {}\nP{} failed, exiting'.format(response.status_code,
                                                                                  json.loads(response.text)[
                                                                                      'message'], url_str))
        return response

    def login(self):
        """Login and set some internal variables
        """
        url_str = self.server_address + '/login'
        json_dict = {'username': self.username, 'password': self.password, 'domain': self.domain}
        response = self._request_and_parse('put', url_str, json_dict)
        self.auth_code = "Basic " + response.content[1:-1]
        self.headers = {"Authorization": self.auth_code, "Content-Type": "application/json"}

    def get_blueprints(self):
        """Get all blueprints details
        :return: <dict> Dict of blueprints and their ids
        """
        url_str = '{}{}'.format(self.server_address, '/v1/blueprints')
        response = self._request_and_parse('get', url_str)

        # parse the output
        parsed_response = json.loads(response.content)
        blueprint_names = [blueprint['name'].encode('utf-8') for blueprint in parsed_response]
        blueprint_ids = [blueprint['id'].encode('utf-8') for blueprint in parsed_response]
        blueprint_dict = dict(zip(blueprint_names, blueprint_ids))

        # return a dictionary of blueprints names and their ids
        return blueprint_dict

    def get_blueprint_id(self, blueprint_name):
        """Return blueprint id, given blueprint name
        :param blueprint_name: Name of the blueprint
        :return: blueprint_id
        """

        # Get all blueprints and see if blueprint_name exists in the list
        blueprints = self.get_blueprints()
        if blueprint_name not in blueprints.iterkeys():
            raise Exception(
                'Blueprint "{}" not found, exiting'.format(blueprint_name))

        # If exists, return name of blueprint
        return blueprints[blueprint_name]

    def get_blueprint_details(self, blueprint_id):
        """Returns a dict of the blueprint, given the blueprint id
        :param blueprint_id: blueprint_id
        :return: dict of name, estimated_setup_duration, description of the blueprint
        """
        url_str = '{}{}{}'.format(self.server_address, '/v1/blueprints/', blueprint_id)
        response = self._request_and_parse('get', url_str)
        parsed_blueprint_details = json.loads(response.content)
        return_dict = {'name': parsed_blueprint_details['name'],
                       'estimated_setup_duration': parsed_blueprint_details['estimated_setup_duration'],
                       'description': parsed_blueprint_details['description']}
        return return_dict

    def get_blueprint_details_by_name(self, blueprint_name):
        """Create a sandbox from the provided blueprint name
        :param blueprint_name: blueprint name
        :return: dict of name, estimated_setup_duration, description of the blueprint
        """
        blueprint_id = self.get_blueprint_id(blueprint_name)
        return self.get_blueprint_details(blueprint_id)

    def start_sandbox(self, blueprint_id, duration, sandbox_name=''):
        """Create a sandbox from the provided blueprint id
        :param blueprint_id: blueprint_id
        :param duration: duration in minutes
        :param sandbox_name: name of the sandbox, same as blueprint if name=''
        :return: if success sandbox_id, else False
        """

        # Do some parameter validation
        try:
            int(duration)
        except ValueError:
            raise Exception('Duration "{}" has to be integer'.format(duration))

        duration = 'PT{}M'.format(duration)
        if sandbox_name == '':
            sandbox_name = self.get_blueprint_details(blueprint_id)['name']

        url_str = '{}{}{}/{}'.format(self.server_address, '/v1/blueprints/', blueprint_id, 'start')
        data_dict = {"duration": duration, "name": sandbox_name}
        response = self._request_and_parse('post', url_str, data_dict=data_dict)
        if response.ok:
            return json.loads(response.content)['id']
        else:
            return response.ok

    def start_sandbox_by_name(self, blueprint_name, duration, sandbox_name=''):
        """Create a sandbox from the provided blueprint name
        :param blueprint_name: blueprint_name
        :param duration: duration in minutes
        :param sandbox_name: sandbox name
        :return: if success sandbox_id, else False
        """
        blueprint_id = self.get_blueprint_id(blueprint_name)
        if sandbox_name == '':
            sandbox_name = blueprint_name
        return self.start_sandbox(blueprint_id, duration, sandbox_name)

    def get_sandboxes(self):
        """Returns a dictionary of all sandboxes name and their ids
        :return: A dict of sandbox ids and names
        """
        url_str = '{}{}'.format(self.server_address, '/v1/sandboxes')
        response = self._request_and_parse('get', url_str)

        # parse the output
        parsed_response = json.loads(response.content)
        sandbox_names = [sandbox['name'].encode('utf-8') for sandbox in parsed_response]
        sandbox_ids = [sandbox['id'].encode('utf-8') for sandbox in parsed_response]
        sandbox_dict = dict(zip(sandbox_ids, sandbox_names))

        # return a dictionary of sandboxes names and their ids
        return sandbox_dict

    def get_sandbox_details(self, sandbox_id):
        """Returns a dictionary of the sandbox, its name, type and state
        :param sandbox_id: <str> Sandbox id
        :return: dictionary of sandbox name, type and state
        """

        # Get info from cloudshell
        url_str = '{}{}{}'.format(self.server_address, '/v1/sandboxes/', sandbox_id)
        response = self._request_and_parse('get', url_str)

        # parse the information
        parsed_blueprint_details = json.loads(response.content)

        # prepare a dictionary to return
        return_dict = {'name': parsed_blueprint_details['name'],
                       'type': parsed_blueprint_details['type'],
                       'state': parsed_blueprint_details['state']}
        return return_dict

    def get_sandboxes_details_by_name(self, sandbox_name):
        """
        :param sandbox_name: Sandbox name
        :return: dictionary of sandbox name, type and state
        """
        return_dict = {}
        sandbox_ids = self.get_sandbox_ids(sandbox_name)
        for sandbox_id in sandbox_ids:
            return_dict[sandbox_id] = self.get_sandbox_details(sandbox_id)
        return return_dict

    def get_sandbox_ids(self, sandbox_name):
        """Returns the sandbox ids for the given sandbox name
        :param sandbox_name: Sandbox name
        :return: Sandbox id
        """
        sandboxes = self.get_sandboxes()
        if sandbox_name not in sandboxes.itervalues():
            raise Exception(
                'Sandbox "{}" not found, exiting'.format(sandbox_name))

        sandbox_ids = [k for k, v in sandboxes.iteritems() if v == sandbox_name]
        return sandbox_ids

    def stop_sandbox(self, sandbox_id):
        """Stop the sandbox given sandbox id
        :param sandbox_id: Sandbox id
        :return: True if success, False if not
        """

        url_str = '{}{}{}/{}'.format(self.server_address, '/v1/sandboxes/', sandbox_id, 'stop')
        response = self._request_and_parse('post', url_str)
        return response.ok

    def stop_sandboxes_by_name(self, sandbox_name):
        """Stop all the sandboxes with the given sandbox name
        :param sandbox_name: Sandbox name
        :return: True if success, False if not
        """
        sandbox_ids = self.get_sandbox_ids(sandbox_name)
        for sandbox_id in sandbox_ids:
            self.stop_sandbox(sandbox_id)


def main():
    usage = """Usage:
    # Init vars
    blueprint_name = 'Sandbox Python API Test'
    sandbox_name = 'Sandbox Python API Test'
    config_file = 'quali_config.json'

    my_sandbox = Sandbox(config_file=config_file)

    my_sandbox.login()

    print my_sandbox.get_blueprints()
    blueprint_id = my_sandbox.get_blueprint_id(blueprint_name=blueprint_name)
    print "Blueprint Id:", blueprint_id
    print my_sandbox.get_blueprint_details(blueprint_id=blueprint_id)
    print my_sandbox.get_blueprint_details_by_name(blueprint_name=blueprint_name)

    print my_sandbox.start_sandbox(blueprint_id=blueprint_id, duration='20', sandbox_name='')
    print my_sandbox.start_sandbox_by_name(blueprint_name=blueprint_name, duration='20', sandbox_name='')
    print my_sandbox.get_sandboxes()
    sandbox_id = my_sandbox.get_sandbox_ids(sandbox_name=sandbox_name)
    print sandbox_id
    print my_sandbox.get_sandbox_details(sandbox_id=sandbox_id[0])
    print my_sandbox.get_sandboxes_details_by_name(sandbox_name=sandbox_name)
    print my_sandbox.stop_sandbox(sandbox_id=sandbox_id[0])
    print my_sandbox.stop_sandboxes_by_name(sandbox_name=sandbox_name)
    """

    print usage


if __name__ == '__main__':
    main()


# # Contents of quali_config.json
# {
#   "server_name": "localhost",
#   "server_port": "82",
#   "username": "USERNAME",
#   "password": "PASSWORD",
#   "domain": "DOMAIN"
# }
