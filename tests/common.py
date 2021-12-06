import json
from random import randint
from time import sleep

from src.cloudshell.sandbox_rest.sandbox_api import SandboxRestApiSession


def pretty_print_response(dict_response):
    json_str = json.dumps(dict_response, indent=4)
    print(f"\n{json_str}")


def random_sleep():
    """ To offset the api calls and avoid rate limit quota """
    random = randint(1, 3)
    print(f"sleeping {random} seconds")
    sleep(random)


def fixed_sleep():
    sleep(3)


def get_blueprint_id_from_name(api: SandboxRestApiSession, bp_name: str):
    res = api.get_blueprint_details(bp_name)
    return res["id"]
