[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python/)
[![Lint and Test](https://github.com/QualiSystemsLab/Sandbox-API-Python/actions/workflows/lint-test.yml/badge.svg)](https://github.com/QualiSystemsLab/Sandbox-API-Python/actions/workflows/lint-test.yml)

# Cloudshell Sandbox Rest Api Client

A python client wrapper around
the [cloudshell sandbox api](https://help.quali.com/Online%20Help/0.0/Portal/Content/API/CS-Snbx-API-Topic.htm?Highlight=sandbox%20api)
. No additional library object wrapping implemented. All methods return the json.loads python object in the shape of the
documented json response. See
the [documentation](https://help.quali.com/Online%20Help/0.0/Portal/Content/API/RefGuides/Sndbx-REST-API/REST-API-V2-Ref-Guide.htm?tocpath=CloudShell%20API%20Guide%7CCloudShell%20Sandbox%20API%7C_____3)
for details.

### Installation

```
pip install cloudshell-sandbox-rest
```

### Basic Usage

```python
from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession

# pull in api user credentials
CS_SERVER = "localhost"
CS_USER = "admin"
CS_PASSWORD = "admin"
CS_DOMAIN = "Global"

TARGET_BLUEPRINT = "<MY_BLUEPRINT_NAME>"
DEPLOYED_SANDBOX_NAME = "My Rest Api Blueprint"

api = SandboxRestApiSession(host=CS_SERVER, username=CS_USER, password=CS_PASSWORD, domain=CS_DOMAIN)
start_response = api.start_sandbox(blueprint_id=TARGET_BLUEPRINT, sandbox_name=DEPLOYED_SANDBOX_NAME)
sandbox_id = start_response["id"]
components_response = api.get_sandbox_components(sandbox_id)

print(f"total components in sandbox: {len(components_response)}")
```

### Context Manager Usage

Using the api session with a context manager "with" statement will log out and invalidate the token for you.

```python
from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession

CS_SERVER = "localhost"
CS_USER = "admin"
CS_PASSWORD = "admin"
CS_DOMAIN = "Global"

TARGET_BLUEPRINT = "<MY_BLUEPRINT_NAME>"
DEPLOYED_SANDBOX_NAME = "My Rest Api Blueprint"

api = SandboxRestApiSession(host=CS_SERVER, username=CS_USER, password=CS_PASSWORD, domain=CS_DOMAIN)

with api:
    start_response = api.start_sandbox(blueprint_id=TARGET_BLUEPRINT, sandbox_name=DEPLOYED_SANDBOX_NAME)
    sandbox_id = start_response["id"]
    components_response = api.get_sandbox_components(sandbox_id)
    print(f"total components in sandbox: {len(components_response)}")
    print(f"session token is: {api.token}")

print(f"session token outside context manager: {api.token}")
```

- NOTE: api login happens during init, not on entering context
- context exit invalidates token

### Instantiate Session with Token

Common use case is for admin to pull user token and start a session on their behalf. This can be done as seen in example
below.

```python
from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession

# admin credentials
CS_SERVER = "localhost"
CS_USER = "admin"
CS_PASSWORD = "admin"
ADMIN_DOMAIN = "Global"

# end user details
TARGET_END_USER = "end user"
TARGET_USER_DOMAIN = "<END_USERS_DOMAIN>"

TARGET_BLUEPRINT = "<MY_BLUEPRINT_NAME>"
DEPLOYED_SANDBOX_NAME = "My Rest Api Blueprint"

admin_api = SandboxRestApiSession(host=CS_SERVER, username=CS_USER, password=CS_PASSWORD, domain=ADMIN_DOMAIN)

with admin_api:
    user_token = admin_api.get_token_for_target_user(TARGET_END_USER)
    user_api = SandboxRestApiSession(host=CS_SERVER, token=user_token, domain=TARGET_USER_DOMAIN)
    with user_api:
        start_response = user_api.start_sandbox(blueprint_id=TARGET_BLUEPRINT, sandbox_name=DEPLOYED_SANDBOX_NAME)
        sandbox_id = start_response["id"]
        components_response = user_api.get_sandbox_components(sandbox_id)
        print(f"total components in sandbox: {len(components_response)}")
```

- Note the use of nested context managers to manage the different session tokens

### License

Free Software: MIT License