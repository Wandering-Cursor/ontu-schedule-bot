"""This is a utils module, it contains Requests and pagination for bot"""

import logging
import math
from urllib.parse import urljoin

import requests
import telegram

from ontu_schedule_bot import classes
from ontu_schedule_bot.enums import Endpoints, Statuses
from ontu_schedule_bot.secret_config import API_URL


# region Requests
class BaseRequester:
    """Defines url for requests and method of request"""

    _url: str = API_URL
    _method: str = "POST"

    session = requests.Session()

    def check_response(self, response: requests.Response):
        """
        Method that checks response
        If we get non 200 response - raises ValueError
        """
        if response.status_code != 200:
            raise ValueError(
                f"Received non OK response ({response.status_code})",
                response,
                response.content,
            )
        return response

    def make_request(self, endpoint: str, **kwargs):
        """Method for making and getting requests"""
        method: str = kwargs.pop("method", "") or self._method
        if not isinstance(
            method,
            (
                str,
                bytes,
            ),
        ):
            raise ValueError("Please don't override method with non str/bytes")

        url = urljoin(self._url, endpoint)

        response = self.session.request(
            url=url,
            method=method,
            data=kwargs.pop("data", None),
            json=kwargs.pop("json", None),
            **kwargs,
        )

        return self.check_response(response=response)


class Getter(BaseRequester):
    """Class that handles getting and sending messages to admin server"""

    def get_chat(self, message_instance: telegram.Message) -> classes.Chat | None:
        """Method to get information about a user"""
        params = {"chat_id": message_instance.chat_id, "topic_id": None}
        if message_instance.is_topic_message:
            params["topic_id"] = message_instance.message_thread_id

        response = self.make_request(
            endpoint=Endpoints.CHAT_INFO.value,
            json=params,
        )

        answer = response.json()
        if not answer:
            return None
        return classes.Chat.from_json(json_dict=answer)

    def get_faculties(self) -> list[classes.Faculty]:
        """Method to get a list of faculties"""
        response = self.make_request(endpoint=Endpoints.FACULTIES_GET.value)

        answer: list[dict] = response.json()
        faculties: list[classes.Faculty] = []
        for faculty in answer:
            faculties.append(classes.Faculty.from_json(faculty))
        return faculties

    def get_groups(self, faculty_name: str) -> list[classes.Group]:
        """This method returns a list of group from faculty name"""
        response = self.make_request(
            endpoint=Endpoints.GROUPS_GET.value, json={"faculty_name": faculty_name}
        )

        answer: list[dict] = response.json()
        groups: list[classes.Group] = []
        for group in answer:
            groups.append(classes.Group.from_json(group))
        return groups

    def get_all_chats(self) -> list[classes.Chat]:
        """This method returns all Telegram Chats with data about them"""
        response = self.make_request(endpoint=Endpoints.CHATS_ALL.value)

        answer: list[dict] = response.json()
        chat_list: list[classes.Chat] = []
        for group in answer:
            chat_list.append(classes.Chat.from_json(group))
        return chat_list

    def get_students_schedule(self, group: classes.Group) -> classes.Schedule:
        """This method gets schedule for some specific group (schedule)"""
        response = self.make_request(
            endpoint=Endpoints.SCHEDULE_GET.value,
            json={"group": group.name, "faculty": group.faculty.name},
        )

        answer: dict = response.json()
        return classes.Schedule.from_json(answer)

    def get_teachers_schedule(
        self, teacher: classes.TeacherForSchedule
    ) -> classes.Schedule:
        """This method gets schedule for some specific teacher (schedule)"""
        response = self.make_request(
            endpoint=Endpoints.TEACHERS_SCHEDULE.value,
            json={"teacher": teacher.external_id},
        )

        answer: dict = response.json()
        return classes.Schedule.from_json(answer)

    def get_schedule(self, subscription: classes.Subscription) -> classes.Schedule:
        """This method returns schedule from subscription"""
        if subscription.group:
            return self.get_students_schedule(group=subscription.group)
        if subscription.teacher:
            return self.get_teachers_schedule(teacher=subscription.teacher)
        raise ValueError("Subscription must have either group or teacher")

    def update_notbot(
        self,
    ) -> bool:
        """Updates notbot on server side

        Returns:
            bool: Was notbot cookie updated. True - yes, False - no
        """
        try:
            self.make_request(
                endpoint=Endpoints.NOTBOT_GET.value, method="GET", timeout=128
            )
            return True
        except (
            ValueError,
            requests.exceptions.RequestException,
            ConnectionError,
        ) as exception:
            logging.exception("Exception occurred when updating notbot.\n%s", exception)
            return False

    def reset_cache(self, group: classes.Group) -> bool:
        """Resets schedule cache for specified group"""
        response = self.make_request(
            endpoint=Endpoints.CACHE_RESET.value,
            json={
                "group": group.name,
                "faculty": group.faculty.name,
            },
        )

        answer: dict = response.json()
        return answer.get("count", 0) >= 0

    def get_batch_schedule(
        self,
    ) -> list[dict[str, classes.Schedule | str | list[int]]]:
        """This method gets schedule for all groups"""
        response = self.make_request(
            endpoint=Endpoints.SCHEDULE_BATCH_GET.value, method="GET"
        )

        answer: list[dict] = response.json()
        result = []
        for group in answer:
            result.append(
                {
                    "chat_info": group["chat_info"],
                    "schedule": classes.Schedule.from_json(group["schedule"]),
                }
            )
        return result

    def get_list_of_departments(self) -> list[classes.Department]:
        """Returns a list of departments"""
        response = self.make_request(
            endpoint=Endpoints.DEPARTMENTS_GET.value, method="GET"
        )

        answer: list[dict] = response.json()

        result: list[classes.Department] = []
        for department in answer:
            result.append(classes.Department.from_json(department))

        return result

    def get_teachers_by_department(
        self, department: classes.Department
    ) -> list[classes.TeacherForSchedule]:
        """Returns a list of teachers for some department"""
        response = self.make_request(
            endpoint=Endpoints.DEPARTMENT_GET.value,
            method="GET",
            params={"department": department.external_id},
        )

        answer: list[dict] = response.json()

        result: list[classes.TeacherForSchedule] = []
        for teacher in answer:
            result.append(
                classes.TeacherForSchedule.from_json(
                    teacher,
                    fetch_department=False,
                )
            )

        return result

    def get_message_campaign(self, campaign_id: str) -> classes.MessageCampaign | None:
        """Returns a Message Campaign from server, if it exists"""
        try:
            response = self.make_request(
                endpoint=Endpoints.MESSAGE_CAMPAIGN_GET.value,
                method="GET",
                params={"campaign_id": campaign_id},
            )
        except ValueError as e:
            logging.warning("Could not find a campaign\n%s", e)
            return None

        answer: dict = response.json()

        return classes.MessageCampaign.from_json(answer)


class Setter(BaseRequester):
    """A class for updating/writing data to"""

    def new_chat(self, message: telegram.Message) -> classes.Chat | dict | None:
        """Creates a new chat, returns response from server"""
        response = self.make_request(
            endpoint=Endpoints.CHAT_CREATE.value,
            json={
                "chat_id": message.chat.id,
                "chat_name": message.chat.effective_name,
                "chat_info": message.to_json(),
                "is_forum": message.chat.is_forum,
                "thread_id": message.message_thread_id,
            },
        )
        answer: dict = response.json()
        if answer.pop("status", "") == Statuses.OK.value:
            return Getter().get_chat(message)
        return answer

    def set_chat_group(
        self,
        message: telegram.Message,
        group: classes.Group,
        is_active: bool = True,
    ) -> classes.Subscription | dict:
        """Updates subscription info for chat"""
        topic_id = message.message_thread_id if message.is_topic_message else None
        response = self.make_request(
            endpoint=Endpoints.CHAT_UPDATE.value,
            json={
                "chat_id": message.chat.id,
                "topic_id": topic_id,
                "group": {"name": group.name, "faculty": group.faculty.name},
                "is_active": is_active,
            },
        )

        answer: dict = response.json()
        if answer.pop("status", "") == Statuses.OK.value:
            return classes.Subscription.from_json(answer)
        return answer

    def set_chat_teacher(
        self,
        message: telegram.Message,
        teacher: classes.TeacherForSchedule,
        is_active: bool = True,
    ):
        """Updates subscription info for chat"""
        topic_id = message.message_thread_id if message.is_topic_message else None
        response = self.make_request(
            endpoint=Endpoints.CHAT_UPDATE.value,
            json={
                "chat_id": message.chat.id,
                "topic_id": topic_id,
                "teacher": {
                    "external_id": teacher.external_id,
                },
                "is_active": is_active,
            },
        )

        answer: dict = response.json()
        if answer.pop("status", "") == Statuses.OK.value:
            return classes.Subscription.from_json(answer)
        return answer


# endregion


# region Pagination
PAGE_SIZE = 10


def get_number_of_pages(list_of_elements: list[object]) -> int:
    """Get's number of pages from some list"""
    return math.ceil(len(list_of_elements) / PAGE_SIZE)


def get_current_page(list_of_elements: list[object], page: int = 0):
    """Returns current part of list divided on pages"""
    if len(list_of_elements) <= PAGE_SIZE:
        return list_of_elements

    return list_of_elements[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]


# endregion


# region Common


def get_chat_from_message(message: telegram.Message):
    """A method to get a chat by message"""
    chat = Getter().get_chat(message)
    if not chat:
        raise ValueError("Будь-ласка - почніть з початку: /start")
    return chat


def split_string(string: str, max_len: int = 4096) -> list[str]:
    """Split into an array of string with size no more than specified"""
    # From https://stackoverflow.com/a/13673133
    string_size = len(string)
    return [string[i : i + max_len] for i in range(0, string_size, max_len)]


def send_message_to_telegram(
    bot_token: str,
    chat_id: int | str,
    topic_id: int | None,
    text: str,
    parse_mode: str | None = "HTML",
) -> bool:
    """Util method to send message via Telegram Bot

    Args:
        bot_token (str): API token of some bot
        chat_id (int): ID of chat to send a message to
        text (str): Text of the message (Currently no support for additional stuff)

    Returns:
        bool: Wether message was sent, or not. True if sent, False if error occurred
    """
    api_endpoint = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        data["parse_mode"] = parse_mode
    if topic_id:
        data["message_thread_id"] = topic_id
    try:
        response = requests.get(
            url=api_endpoint,
            data=data,
            timeout=5,
        )

        if response.status_code != 200:
            raise ValueError("Got non 200 response", response)

        # We've sent the message
        return True
    except (
        requests.exceptions.RequestException,
        ConnectionError,
        ValueError,
    ) as exception:
        logging.exception("Could not send message\nException: %s", exception)
        return False


# endregion
