"""Describes a MessageCampaign - mass-sending object for Administrators"""
from classes.base import BaseClass


class MessageCampaign(BaseClass):
    """MessageCampaign consists of a list of chats and a message from administrators"""

    to_chats: list[str]
    message: str

    @classmethod
    def from_json(cls, json_dict: dict) -> "MessageCampaign":
        required_params = ["to_chats", "message"]

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict, required_params=required_params
        )

        obj = cls.make_object(parsed_params)

        return obj
