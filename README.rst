CloudShell Sandbox API Wrapper
==============================

Installation
*************
::

    pip install cloudshell_sandboxapi_wrapper

Example Usage
**************
::

    from cloudshell_sandboxapi_wrapper.SandboxAPI import SandboxAPI
    sandbox = SandboxAPI(host=SERVER_NAME, username=USERNAME, password=PASSWORD, domain=DOMAIN, port=SERVER_PORT)
    blueprints = sandbox.get_blueprints()
    blueprint_id = sandbox.get_blueprint_details(blueprint_id=BLUEPRINT_NAME)['id']
    sandbox_id = sandbox.start_sandbox(BLUEPRINT_NAME, PT23H, SANDBOX_NAME)
    sandbox.stop_sandbox(sandbox_id)

|

:Note:
  Tested on cloudshell 9.3 with Python 2.7/3.7/3.8.
  For API details, please refer to CloudShell Sandbox API help: `CloudShell Sandbox API <https://help.quali.com/Online%20Help/9.3/Api-Guide/Content/API/CS-Snbx-API-Topic.htm>`_

|
