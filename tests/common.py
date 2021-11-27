import json

from cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


def pretty_print_response(dict_response):
    json_str = json.dumps(dict_response, indent=4)
    print(f"\n{json_str}")


def get_blueprint_id_from_name(api: SandboxRestApiSession, bp_name: str):
    res = api.get_blueprint_details(bp_name)
    return res["id"]
