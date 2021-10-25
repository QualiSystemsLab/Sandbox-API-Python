from requests import Response


class SandboxRestException(Exception):
    """ Base Exception Class inside Rest client class """
    def __init__(self, msg: str, response: Response = None):
        self.msg = msg
        self.response = response

    def __str__(self):
        return self._format_err_msg(self.msg, self.response)

    def _format_err_msg(self, custom_err_msg="Failed Api Call", response: Response = None) -> str:
        err_msg = f"Sandbox API Error: {custom_err_msg}"

        if response:
            err_msg += f"\n{self._format_response_msg(response)}"

    @staticmethod
    def _format_response_msg(response: Response):
        return (f"Response: {response.status_code}, Reason: {response.reason}\n"
                f"Request URL: {response.request.url}\n"
                f"Request Headers: {response.request.headers}")


class SandboxRestAuthException(SandboxRestException):
    """ Failed auth action """
    pass
