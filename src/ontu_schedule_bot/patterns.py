"""Defines patterns for callbacks"""


def manage_subscription_pattern(callback_data: object) -> bool:
    """Pattern for manage_subscription"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "manage_subscription")


def manage_subscription_groups_pattern(callback_data: object) -> bool:
    """Pattern for manage_subscription_groups"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "manage_groups")


def manage_subscription_teachers_pattern(callback_data: object) -> bool:
    """Pattern for manage_subscription_teachers"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "manage_teachers")


def remove_subscription_items_pattern(callback_data: object) -> bool:
    """Pattern for remove_subscription_items"""
    return bool(
        isinstance(callback_data, tuple) and callback_data[0] == "remove_subscription_items"
    )


def remove_subscription_item_pattern(callback_data: object) -> bool:
    """Pattern for remove_subscription_item"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "remove_subscription_item")


def add_subscription_group_pattern(callback_data: object) -> bool:
    """Pattern for add_subscription_group"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "add_subscription_group")


def add_subscription_teacher_pattern(callback_data: object) -> bool:
    """Pattern for add_subscription_teacher"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "add_subscription_teacher")


def select_faculty_pattern(callback_data: object) -> bool:
    """Pattern for select_faculty"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "select_faculty")


def select_department_pattern(callback_data: object) -> bool:
    """Pattern for select_department"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "select_department")


def add_subscription_item_pattern(callback_data: object) -> bool:
    """Pattern for add_subscription_item"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "add_subscription_item")


def start_pattern(callback_data: object) -> bool:
    """Pattern for start"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "start")


def get_week_schedule_pattern(callback_data: object) -> bool:
    """Pattern for get_week_schedule"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "get_week_schedule")


def get_schedule_pattern(callback_data: object) -> bool:
    """Pattern for get_schedule"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "get_schedule")


def get_pair_details_pattern(callback_data: object) -> bool:
    """Pattern for pair_details"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "get_pair_details")


def toggle_subscription_pattern(callback_data: object) -> bool:
    """Pattern for toggle_subscription"""
    return bool(isinstance(callback_data, tuple) and callback_data[0] == "toggle_subscription")
