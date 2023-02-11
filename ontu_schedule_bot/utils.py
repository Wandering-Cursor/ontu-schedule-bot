from urllib.parse import urljoin
import requests

from secret_config import API_URL
from enums import Statuses, Endpoints


import classes

import telegram

# region Requests
class BaseRequester:
    """Defines url for requests and method of request"""
    _url: str = API_URL
    _method: str = "POST"

    session = requests.Session()

    def _check_response(self, response: requests.Response):
        if response.status_code != 200:
            raise ValueError(
                f"Recieved non OK response ({response.status_code}): {response}",
                response
            )
        return response

    def make_request(self, endpoint: str, **kwargs):
        """Method for making and getting requests"""
        method: str = self._method or kwargs.pop('method', '')
        if not isinstance(method, (str, bytes, )):
            raise ValueError(
                "Please don't override method with non str/bytes"
            )

        response = self.session.request(
            url=urljoin(self._url, endpoint),
            method=method,
            data=kwargs.pop('data', None),
            json=kwargs.pop('json', None),
            **kwargs
        )

        return self._check_response(response=response)


class Getter(BaseRequester):
    """Class that handles getting and sending messages to admin server"""

    def get_chat(self, user_id: int):
        """Method to get information about a user"""
        response = self.make_request(
            endpoint=Endpoints.CHAT_INFO.value,
            json={
                'user_id': user_id
            }
        )

        answer = response.json()
        if not answer:
            return None
        return classes.Chat.from_json(json_dict=answer)

    def get_faculties(self):
        """Method to get a list of faculties"""
        response = self.make_request(
            endpoint=Endpoints.FACULTIES_GET.value
        )

        answer: list[dict] = response.json()
        faculties: list[classes.Faculty] = []
        for faculty in answer:
            faculties.append(
                classes.Faculty.from_json(
                    faculty
                )
            )
        return faculties

    def get_groups(self, faculty_name: str):
        response = self.make_request(
            endpoint=Endpoints.GROUPS_GET.value,
            json={
                "faculty_name": faculty_name
            }
        )

        answer: list[dict] = response.json()
        groups: list[classes.Group] = []
        for group in answer:
            groups.append(
                classes.Group.from_json(
                    group
                )
            )
        return groups


class Setter(BaseRequester):
    """A class for updating/writing data to admin"""

    def new_chat(self, chat: telegram.Chat) -> classes.Chat|dict|None:
        """Creates a new chat, returns response from server"""
        response = self.make_request(
            endpoint=Endpoints.CHAT_CREATE.value,
            json={
                'chat_id': chat.id,
                'chat_name': chat.effective_name,
                'chat_info': chat.to_json(),
            }
        )
        answer: dict = response.json()
        if answer.get('status', '') == Statuses.OK.value:
            return Getter().get_chat(chat.id)
        return answer

# endregion
