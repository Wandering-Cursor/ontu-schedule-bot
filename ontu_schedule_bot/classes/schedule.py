"""Describes schedule"""
import datetime

from classes.base import BaseClass, pair_times

from classes.pair import Pair


MAX_PAIRS = 6

day_names = {
    0: "Понеділок",
    1: "Вівторок",
    2: "Середа",
    3: "Четверг",
    4: "П'ятниця",
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

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ['days']

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params
        )

        days: dict[str, list[Pair]] = {}
        json_days: dict[str, list[dict]] = parsed_params.pop('days')
        for day_name, pairs in json_days.items():
            days[day_name] = [
                Pair.from_json(pair) for pair in pairs
            ]

        obj = cls.make_object(parsed_params)
        obj.days = days
        return obj

    def _get_next_pair_index(
            self,
            pair_no: int | None = None,
            hour_minute_tuple: tuple[int, int] | None = None) -> tuple[int, bool]:
        """If we know pair_no - return the next pair"""
        next_pair_no = None
        day_changed = False
        if pair_no:
            next_pair_no = pair_no + 1

        if hour_minute_tuple:
            next_pair_no = _next_pair_no_from_time(hour_minute_tuple)

        if next_pair_no is None:
            raise ValueError("Could not get_next_pair_index", pair_no, hour_minute_tuple)

        if next_pair_no < 0 or next_pair_no > MAX_PAIRS:
            # Basically if next_pair_no_from_time returns -1 - it means it's not today
            # If next_pair_no is > MAX_PAIRS - it's the same thing
            day_changed = True
            next_pair_no = 1

        return (next_pair_no, day_changed)

    def __get_next_day(self, day_no: int):
        day_no += 1
        if day_no >= 6:
            day_no = 0
        return day_no

    def _check_should_stop(self, next_pair: Pair | None, day_no: int, initial_day_no: int):
        if next_pair:
            return True
        day_no = self.__get_next_day(day_no=day_no)
        if day_no == initial_day_no:
            return True
        return False

    def get_next_pair(
            self,
            find_all: bool = True) -> tuple[Pair, str] | None:
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
        now = datetime.datetime.now()
        hour_minute_tuple = (now.hour, now.minute)

        initial_day_no = now.weekday()
        initial_pair_no, _ = self._get_next_pair_index(hour_minute_tuple=hour_minute_tuple)

        day_no, pair_no = initial_day_no, initial_pair_no

        next_pair = None
        while True:
            pairs_of_day = self.days.get(day_names.get(day_no, ""))
            if not pairs_of_day and not find_all:
                return None
            if not pairs_of_day:
                day_no = self.__get_next_day(day_no=day_no)
                pair_no = 0
                continue
            for pair in pairs_of_day:
                if pair.pair_index >= pair_no:
                    if pair.has_lessons:
                        next_pair = pair
                        break
                    if not find_all:
                        return None
            if self._check_should_stop(
                    next_pair=next_pair,
                    day_no=day_no,
                    initial_day_no=initial_day_no):
                break
            day_no = self.__get_next_day(day_no=day_no)
            pair_no = 0

        if not next_pair:
            raise ValueError(
                "Could not get next pair",
                pairs_of_day,
                pair_no
            )

        return next_pair, day_names.get(day_no, "")
