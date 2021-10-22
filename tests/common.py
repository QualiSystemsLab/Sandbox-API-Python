import json

DUT_RESOURCE = "DUT_1"
DEFAULT_BLUEPRINT_TEMPLATE = "CloudShell Sandbox Template"
HEALTH_CHECK_COMMAND = "health_check"


def pretty_print_response(dict_response):
    json_str = json.dumps(dict_response, indent=4)
    print(f"\n{json_str}")
