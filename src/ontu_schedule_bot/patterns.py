"""Defines patterns for callbacks"""

import functools
from collections.abc import Callable, Sequence
from enum import StrEnum

from ontu_schedule_bot.utils import data_to_string, string_to_data


def convert_data_to_object_decorator(func: Callable) -> Callable:
    """Decorator to convert callback data to object"""

    @functools.wraps(func)
    def wrapper(callback_data: str) -> bool:
        try:
            data = Patterns.load(callback_data)
        except (ValueError, TypeError):
            return False
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

    WEEK_SCHEDULE = "ws"
    GET_SCHEDULE = "gs"
    GET_PAIR_DETAILS = "gpd"

    NOOP = "noop"

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

    @property
    def to_remove_translation(self) -> str:
        translations = {
            SubscriptionItemType.GROUP: "групу",
            SubscriptionItemType.TEACHER: "викладача",
        }
        return translations[self]


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

    return all(
        [
            callback_data[0] == Patterns.REMOVE_SUBSCRIPTION_ITEMS,
            callback_data[1] in SubscriptionItemType,
        ]
    )


@convert_data_to_object_decorator
def remove_subscription_item_pattern(callback_data: Sequence[Patterns | object] | Patterns) -> bool:
    """Pattern for remove_subscription_item"""
    assert isinstance(callback_data, Sequence)

    return all(
        [
            callback_data[0] == Patterns.REMOVE_ITEM,
            callback_data[1] in SubscriptionItemType,
        ]
    )


@convert_data_to_object_decorator
def add_subscription_group_pattern(callback_data: Sequence[Patterns | object] | Patterns) -> bool:
    """Pattern for add_subscription_group"""
    assert isinstance(callback_data, Sequence)

    if len(callback_data) != 2:  # noqa: PLR2004
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

    if len(callback_data) != 2:  # noqa: PLR2004
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

    if len(callback_data) != 3:  # noqa: PLR2004
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

    if len(callback_data) != 3:  # noqa: PLR2004
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

    if len(callback_data) != 3:  # noqa: PLR2004
        return False

    return all(
        [
            callback_data[0] == Patterns.ADD_SUBSCRIPTION_ITEM,
            callback_data[1] in (SubscriptionItemType.GROUP, SubscriptionItemType.TEACHER),
            isinstance(callback_data[2], str),  # ID of a group or a teacher
        ]
    )


@convert_data_to_object_decorator
def start_pattern(callback_data: object) -> bool:
    """Pattern for start"""
    if not isinstance(callback_data, str):
        return False

    return bool(callback_data == Patterns.START)


@convert_data_to_object_decorator
def get_week_schedule_pattern(callback_data: object) -> bool:
    """Pattern to get week's worth of schedule"""
    if isinstance(callback_data, str):
        return bool(callback_data == Patterns.WEEK_SCHEDULE)

    if isinstance(callback_data, Sequence):
        return bool(callback_data[0] == Patterns.WEEK_SCHEDULE)

    return False


@convert_data_to_object_decorator
def get_schedule_pattern(callback_data: object) -> bool:
    """Pattern for get_schedule"""
    if not isinstance(callback_data, Sequence):
        return False

    if len(callback_data) != 3:  # noqa: PLR2004
        return False

    return all(
        [
            callback_data[0] == Patterns.GET_SCHEDULE,
            isinstance(callback_data[1], int),  # Date in ordinal format
            isinstance(callback_data[2], str),  # Short ID of a group or a teacher
        ]
    )


@convert_data_to_object_decorator
def get_pair_details_pattern(callback_data: object) -> bool:
    """Pattern for pair_details"""
    if not isinstance(callback_data, Sequence):
        return False

    if len(callback_data) != 4:  # noqa: PLR2004
        return False

    return all(
        [
            callback_data[0] == Patterns.GET_PAIR_DETAILS,
            isinstance(callback_data[1], int),  # Pair number
            isinstance(callback_data[2], int),  # Date in ordinal format
            isinstance(callback_data[3], str),  # Short ID of a group or a teacher
        ]
    )


@convert_data_to_object_decorator
def toggle_subscription_pattern(callback_data: object) -> bool:
    """Pattern for toggle_subscription"""
    if not isinstance(callback_data, str):
        return False

    return bool(callback_data == Patterns.TOGGLE_SUBSCRIPTION)


@convert_data_to_object_decorator
def noop_pattern(callback_data: object) -> bool:
    """Pattern for noop"""
    if not isinstance(callback_data, str):
        return False

    return bool(callback_data == Patterns.NOOP)
