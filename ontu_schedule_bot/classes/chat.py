"""This module contains chat classes"""

from classes.base import BaseClass

from classes.subscription import Subscription

class Chat(BaseClass):
    """Describes a chat with a subscription for schedule"""
    chat_id: int
    chat_name: str

    subscription: Subscription|None = None

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ['chat_id', 'chat_name', ]
        optional_params = ['subscription']

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params,
            optional_params=optional_params
        )

        subscription_json = parsed_params.pop('subscription', None)
        subscription: Subscription|None = None
        if subscription_json:
            subscription = Subscription.from_json(
                json_dict=subscription_json
            )

        obj = cls.make_object(parsed_params)
        if subscription:
            obj.subscription = subscription
        return obj