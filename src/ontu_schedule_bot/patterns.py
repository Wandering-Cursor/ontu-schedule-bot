"""Defines patterns for callbacks"""


def manage_subscription_pattern(callback_data):
    """Pattern for manage_subscription"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "manage_subscription":
            return True
    return False


def manage_subscription_groups_pattern(callback_data):
    """Pattern for manage_subscription_groups"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "manage_groups":
            return True
    return False


def manage_subscription_teachers_pattern(callback_data):
    """Pattern for manage_subscription_teachers"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "manage_teachers":
            return True
    return False


def remove_subscription_items_pattern(callback_data):
    """Pattern for remove_subscription_items"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "remove_subscription_items":
            return True
    return False


def remove_subscription_item_pattern(callback_data):
    """Pattern for remove_subscription_item"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "remove_subscription_item":
            return True
    return False


def add_subscription_group_pattern(callback_data):
    """Pattern for add_subscription_group"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "add_subscription_group":
            return True
    return False


def add_subscription_teacher_pattern(callback_data):
    """Pattern for add_subscription_teacher"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "add_subscription_teacher":
            return True
    return False


def select_faculty_pattern(callback_data):
    """Pattern for select_faculty"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "select_faculty":
            return True
    return False


def select_department_pattern(callback_data):
    """Pattern for select_department"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "select_department":
            return True
    return False


def add_subscription_item_pattern(callback_data):
    """Pattern for add_subscription_item"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "add_subscription_item":
            return True
    return False


def start_pattern(callback_data):
    """Pattern for start"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "start":
            return True
    return False


def get_schedule_pattern(callback_data):
    """Pattern for get_schedule"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "get_schedule":
            return True
    return False


def get_pair_details_pattern(callback_data):
    """Pattern for pair_details"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "get_pair_details":
            return True
    return False


def toggle_subscription_pattern(callback_data):
    """Pattern for toggle_subscription"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "toggle_subscription":
            return True
    return False
