import json


def pretty_print_response(dict_response):
    json_str = json.dumps(dict_response, indent=4)
    print(f"\n{json_str}")
