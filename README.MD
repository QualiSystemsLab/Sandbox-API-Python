[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python/)
[![PyPI version](https://badge.fury.io/py/cloudshell-sandboxapi-wrapper.svg)](https://badge.fury.io/py/cloudshell-sandboxapi-wrapper)

# Cloudshell Sandbox Rest Api Client
A python client wrapper around the [cloudshell sandbox api](https://help.quali.com/Online%20Help/0.0/Portal/Content/API/CS-Snbx-API-Topic.htm?Highlight=sandbox%20api).
This client provides an object-oriented interface to instantiating an api session and interacting with the endpoints.

No additional library object wrapping implemented. All methods return the json.loads python object in the shape of the documented json response. See the [documentation](https://help.quali.com/Online%20Help/0.0/Portal/Content/API/RefGuides/Sndbx-REST-API/REST-API-V2-Ref-Guide.htm?tocpath=CloudShell%20API%20Guide%7CCloudShell%20Sandbox%20API%7C_____3) 
for details. 

### Installation

```
pip install cloudshell-sandbox-rest
```

### Basic Usage
```python
from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession
api = SandboxRestApiSession(host="localhost", username="admin", password="admin", domain="Global")
start_response = api.start_sandbox(blueprint_id="<MY_BLUEPRINT_NAME>", sandbox_name="My Rest Api Blueprint")
sandbox_id = start_response["id"]
components_response = api.get_sandbox_components(sandbox_id)
print(f"total components in sandbox: {len(components_response)}")
```

### Context Manager Usage
Using the api session with a context manager "with" statement will log out and invalidate the token for you.

```python
from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession

api = SandboxRestApiSession(host="localhost", username="admin", password="admin", domain="Global")

with api:
    start_response = api.start_sandbox(blueprint_id="<MY_BLUEPRINT_NAME>", sandbox_name="My Rest Api Blueprint")
    sandbox_id = start_response["id"]
    components_response = api.get_sandbox_components(sandbox_id)
    print(f"total components in sandbox: {len(components_response)}")
    print(f"session token is: {api.token}")

print(f"session token outside context manager: {api.token}")
```
- NOTE: api login happens during init, not on entering context
- context exit invalidates token

### Instantiate Session with Token
Common use case is for admin to pull user token and start a session on their behalf. This can be done as seen in example below.
```python
from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession

admin_api = SandboxRestApiSession(host="localhost", username="admin", password="admin", domain="Global")

with admin_api:
    user_token = admin_api.get_token_for_target_user("end_user")
    user_api = SandboxRestApiSession(host="localhost", token=user_token, domain="<END_USERS_DOMAIN>")
    with user_api:
        start_response = user_api.start_sandbox(blueprint_id="<MY_BLUEPRINT_NAME>", sandbox_name="My Rest Api Blueprint")
        sandbox_id = start_response["id"]
        components_response = user_api.get_sandbox_components(sandbox_id)
        print(f"total components in sandbox: {len(components_response)}")
```
- Note the use of nested context managers to manage the different session tokens

### License 
Free Software: MIT License