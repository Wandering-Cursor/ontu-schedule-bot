"""Describes schedule"""

import datetime

import pytz

from ontu_schedule_bot.enums import pair_times

from .base import BaseClass
from .day import Day
from .pair import Pair

MAX_PAIRS = 8

day_names = {
    0: "Понеділок",
    1: "Вівторок",
    2: "Середа",
    3: "Четвер",
    4: "П`ятниця",  # ` typo is from rozklad.ontu.edu.ua
    5: "Субота",
    6: "Неділя",
}


def _next_pair_no_from_time(hour_minute_tuple: tuple[int, int]) -> int:
    """Method that get's next pair_no based on time tuple (should not be raw used)"""
    i = 0
    hour = hour_minute_tuple[0]
    minute = hour_minute_tuple[1]
    for time_dict in pair_times:
        i += 1
        if hour < time_dict["hour"]:
            break
        if time_dict["hour"] == hour and minute < time_dict["minute"]:
            break
    else:
        i = -1
    return i


class Schedule(BaseClass):
    """
    Schedule dataclass
    Schedule keeps days (week to be precise)
    Days keep pairs
    Pairs - lessons

    This class provides a method to get next pair
    (and will provide a way to get a schedule for whole week later on)
    """

    days: dict[str, list[Pair]]

    day_names = day_names

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ["days"]

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict, required_params=required_params
        )

        days: dict[str, list[Pair]] = {}
        json_days: dict[str, list[dict]] = parsed_params.pop("days")
        for day_name, pairs in json_days.items():
            days[day_name] = [Pair.from_json(pair) for pair in pairs]

        obj = cls.make_object(parsed_params)
        obj.days = days
        return obj

    def _get_next_pair_index(
        self,
        pair_no: int | None = None,
        hour_minute_tuple: tuple[int, int] | None = None,
    ) -> tuple[int, bool]:
        """If we know pair_no - return the next pair"""
        next_pair_no = None
        day_changed = False
        if pair_no:
            next_pair_no = pair_no + 1

        if hour_minute_tuple:
            next_pair_no = _next_pair_no_from_time(hour_minute_tuple)

        if next_pair_no is None:
            raise ValueError(
                "Could not get_next_pair_index", pair_no, hour_minute_tuple
            )

        if next_pair_no < 0 or next_pair_no > MAX_PAIRS:
            # Basically if next_pair_no_from_time returns -1 - it means it's not today
            # If next_pair_no is > MAX_PAIRS - it's the same thing
            day_changed = True
            next_pair_no = 1

        return (next_pair_no, day_changed)

    def __get_next_day(self, day_no: int):
        day_no += 1
        if day_no > 6:
            day_no = 0
        return day_no

    def _check_should_stop(
        self,
        next_pair: Pair | None,
        day_no: int,
        initial_day_no: int,
    ) -> tuple[bool, str]:
        if next_pair:
            return True, "Пару знайдено"
        day_no = self.__get_next_day(day_no=day_no)
        if day_no == initial_day_no:
            return True, "Немає розкладу на весь тиждень"
        if day_no < initial_day_no:
            if initial_day_no != 6:
                return (
                    True,
                    "Наступна пара в понеділок (очікуйте неділі для перегляду розкладу)",
                )
        return (
            False,
            "Якщо ви це бачите, то когось треба лупити. Пишіть @man_with_a_name",
        )

    def _get_initial(
        self, initial_day_no: int, initial_pair_no: int, day_changed: bool
    ) -> tuple[int, int]:
        if day_changed:
            initial_day_no = self.__get_next_day(day_no=initial_day_no)
            initial_pair_no = 0
        return initial_day_no, initial_pair_no

    def get_next_pair(self, find_all: bool = True) -> tuple[Pair | None, str]:
        """
        Returns next pair
        First - tries to get the actual next pair with lessons
            Like if it's 11:00 - tries to get 11:30 pair
        If fails - tries to get the next pair with lessons in a day
            For example - students have first and sixth pairs,
            if it's past first pair - will return sixth one
        If fails still - tries to get the next pair from next pair, going trough a week
            For example - students have pairs in monday (1st and 6th), and in friday (3rd)
            If it's past sixth pair of monday - will return third pair for friday
        If no pairs can be found still - raises a ValueError
        """
        # pylint: disable = R0911, R0912
        # Refactor this method
        now = datetime.datetime.now(tz=pytz.timezone("Europe/Kyiv"))
        hour_minute_tuple = (now.hour, now.minute)

        initial_day_no = now.weekday()
        initial_pair_no, day_changed = self._get_next_pair_index(
            hour_minute_tuple=hour_minute_tuple
        )

        if not find_all and day_changed:
            return None, ""

        day_no, pair_no = self._get_initial(
            initial_day_no=initial_day_no,
            initial_pair_no=initial_pair_no,
            day_changed=day_changed,
        )

        next_pair = None
        while True:
            pairs_of_day = self.days.get(day_names.get(day_no, ""))
            if not pairs_of_day and not find_all:
                return None, ""
            if not pairs_of_day:
                day_no = self.__get_next_day(day_no=day_no)
                should_stop, message = self._check_should_stop(
                    next_pair=next_pair, day_no=day_no, initial_day_no=initial_day_no
                )
                if should_stop:
                    return None, message
                pair_no = 0
                continue
            for pair in pairs_of_day:
                if pair.pair_no >= pair_no:
                    if pair.has_lessons:
                        next_pair = pair
                        break
                    # If pair exists, but there's no lesson
                    if not find_all:
                        return None, ""
            else:
                # If we don't need to find pair in all time
                if not find_all:
                    return None, ""
            should_stop, message = self._check_should_stop(
                next_pair=next_pair, day_no=day_no, initial_day_no=initial_day_no
            )
            if next_pair:
                return next_pair, day_names.get(day_no, "")
            if not next_pair and should_stop:
                return None, message
            day_no = self.__get_next_day(day_no=day_no)
            pair_no = 0

    def get_week_representation(self) -> list[Day]:
        """Returns a list of days represented as strings"""
        days: list[Day] = []
        for day_name, pairs in self.days.items():
            days.append(Day(day_name=day_name, pairs=pairs))
        return days

    def get_today_representation(
        self, today: datetime.date | None = None
    ) -> Day | None:
        """Method to get schedule of current day
        You can override what `current` means

        Args:
            today (datetime.date | None): If not passed = datetime.date.today()

        Returns:
            Day: A day object with schedule
        """
        if not isinstance(today, datetime.date):
            today = datetime.date.today()

        weekday = today.weekday()
        week = self.get_week_representation()

        try:
            return week[weekday]
        except IndexError:
            return None
