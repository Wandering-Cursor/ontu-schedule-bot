"""Defines patterns for callbacks"""

import functools
from collections.abc import Callable, Sequence
from enum import StrEnum

from ontu_schedule_bot.utils import data_to_string, string_to_data


def convert_data_to_object_decorator(func: Callable) -> Callable:
    """Decorator to convert callback data to object"""

    @functools.wraps(func)
    def wrapper(callback_data: str) -> bool:
        data = Patterns.load(callback_data)
        return func(data)

    return wrapper


class Patterns(StrEnum):
    START = "start"

    MANAGE_SUBSCRIPTION = "manage_subscription"
    MANAGE_GROUPS = "manage_groups"
    MANAGE_TEACHERS = "manage_teachers"

    TOGGLE_SUBSCRIPTION = "toggle_subscription"

    # Use parameters
    REMOVE_SUBSCRIPTION_ITEMS = "remove_subscription_items"
    REMOVE_ITEM = "ri"

    SELECT_FACULTY = "sf"
    SELECT_DEPARTMENT = "sd"

    ADD_SUBSCRIPTION_ITEM = "asi"

    def with_args(self, *args: object) -> str:
        if not args:
            return data_to_string(self)

        return data_to_string((self.value, *args))

    @classmethod
    def load(cls, data: str) -> "Sequence[Patterns | object] | Patterns":
        value = string_to_data(data)

        if isinstance(value, str):
            return cls(value)

        return tuple(
            cls(item) if isinstance(item, str) and item in cls._value2member_map_ else item
            for item in value
        )


class SubscriptionItemType(StrEnum):
    GROUP = "g"
    TEACHER = "t"


@convert_data_to_object_decorator
def manage_subscription_pattern(callback_data: Sequence[Patterns | object] | Patterns) -> bool:
    """Pattern for manage_subscription"""
    return bool(callback_data == Patterns.MANAGE_SUBSCRIPTION)


@convert_data_to_object_decorator
def manage_subscription_groups_pattern(
    callback_data: Sequence[Patterns | object] | Patterns,
) -> bool:
    """Pattern for manage_subscription_groups"""
    return bool(callback_data == Patterns.MANAGE_GROUPS)


@convert_data_to_object_decorator
def manage_subscription_teachers_pattern(
    callback_data: Sequence[Patterns | object] | Patterns,
) -> bool:
    """Pattern for manage_subscription_teachers"""
    return bool(callback_data == Patterns.MANAGE_TEACHERS)


@convert_data_to_object_decorator
def remove_subscription_items_pattern(
    callback_data: Sequence[Patterns | object] | Patterns,
) -> bool:
    """Pattern for remove_subscription_items"""
    if isinstance(callback_data, str):
        return callback_data == Patterns.REMOVE_SUBSCRIPTION_ITEMS

    assert isinstance(callback_data, Sequence)

    return bool(callback_data[0] == Patterns.REMOVE_SUBSCRIPTION_ITEMS)


@convert_data_to_object_decorator
def remove_subscription_item_pattern(callback_data: Sequence[Patterns | object] | Patterns) -> bool:
    """Pattern for remove_subscription_item"""
    assert isinstance(callback_data, Sequence)

    return bool(callback_data[0] == Patterns.REMOVE_ITEM)


@convert_data_to_object_decorator
def add_subscription_group_pattern(callback_data: Sequence[Patterns | object] | Patterns) -> bool:
    """Pattern for add_subscription_group"""
    assert isinstance(callback_data, Sequence)

    if len(callback_data) != 2:
        return False

    return all(
        [
            callback_data[0] == Patterns.ADD_SUBSCRIPTION_ITEM,
            callback_data[1] == SubscriptionItemType.GROUP,
        ]
    )


@convert_data_to_object_decorator
def add_subscription_teacher_pattern(callback_data: Sequence[Patterns | object] | Patterns) -> bool:
    """Pattern for add_subscription_teacher"""
    assert isinstance(callback_data, Sequence)

    if len(callback_data) != 2:
        return False

    return all(
        [
            callback_data[0] == Patterns.ADD_SUBSCRIPTION_ITEM,
            callback_data[1] == SubscriptionItemType.TEACHER,
        ]
    )


@convert_data_to_object_decorator
def select_faculty_pattern(callback_data: Sequence[Patterns | object] | Patterns) -> bool:
    """Pattern for select_faculty"""
    assert isinstance(callback_data, Sequence)

    if len(callback_data) != 3:
        return False

    return all(
        [
            callback_data[0] == Patterns.SELECT_FACULTY,
            isinstance(callback_data[1], str),  # Faculty ID
            isinstance(callback_data[2], int),  # Page number
        ]
    )


@convert_data_to_object_decorator
def select_department_pattern(callback_data: Sequence[Patterns | object] | Patterns) -> bool:
    """Pattern for select_department"""
    assert isinstance(callback_data, Sequence)

    if len(callback_data) != 3:
        return False

    return all(
        [
            callback_data[0] == Patterns.SELECT_DEPARTMENT,
            isinstance(callback_data[1], str),  # Department ID
            isinstance(callback_data[2], int),  # Page number
        ]
    )


@convert_data_to_object_decorator
def add_subscription_item_pattern(callback_data: Sequence[Patterns | object] | Patterns) -> bool:
    """Pattern for add_subscription_item"""
    assert isinstance(callback_data, Sequence)

    if len(callback_data) != 3:
        return False

    return all(
        [
            callback_data[0] == Patterns.ADD_SUBSCRIPTION_ITEM,
            callback_data[1] in (SubscriptionItemType.GROUP, SubscriptionItemType.TEACHER),
        ]
    )


def start_pattern(callback_data: object) -> bool:
    """Pattern for start"""
    assert isinstance(callback_data, str)

    return bool(callback_data == Patterns.START)


def get_week_schedule_pattern(callback_data: object) -> bool:
    """Pattern for get_week_schedule"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "get_week_schedule")


def get_schedule_pattern(callback_data: object) -> bool:
    """Pattern for get_schedule"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "get_schedule")


def get_pair_details_pattern(callback_data: object) -> bool:
    """Pattern for pair_details"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "get_pair_details")


@convert_data_to_object_decorator
def toggle_subscription_pattern(callback_data: object) -> bool:
    """Pattern for toggle_subscription"""
    assert isinstance(callback_data, str)

    return bool(callback_data == Patterns.TOGGLE_SUBSCRIPTION)
