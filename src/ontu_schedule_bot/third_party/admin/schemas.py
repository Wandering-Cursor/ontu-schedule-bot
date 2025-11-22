import datetime
import pydantic

from ontu_schedule_bot.third_party.admin.enums import Platform

class Schema(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        from_attributes=True,
    )

class Chat(Schema):
    uuid: pydantic.UUID4

    platform: Platform

    platform_chat_id: str

    title: str | None
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    additional_info: dict | None


class CreateChatRequest(Schema):
    platform: Platform

    platform_chat_id: str

    title: str | None = pydantic.Field(
        default=None,
        description="Title of the chat.",
    )
    username: str | None = pydantic.Field(
        default=None,
        description="Username of the chat.",
    )
    first_name: str | None = pydantic.Field(
        default=None,
        description="First name of the chat.",
    )
    last_name: str | None = pydantic.Field(
        default=None,
        description="Last name of the chat.",
    )
    language_code: str | None = pydantic.Field(
        default=None,
        description="Language code of the chat.",
    )
    additional_info: dict | None = pydantic.Field(
        default=None,
        description="Additional information about the chat.",
    )

class Faculty(Schema):
    uuid: pydantic.UUID4

    short_name: str

class Group(Schema):
    uuid: pydantic.UUID4

    short_name: str
    faculty: Faculty

class Department(Schema):
    uuid: pydantic.UUID4

    short_name: str
    full_name: str

class Teacher(Schema):
    uuid: pydantic.UUID4

    short_name: str
    full_name: str

    departments: list[Department]

class ScheduleTeacherInfo(Schema):
    """
    This class is used in palces that can only get
    teacher information from Schedule API.

    They don't have ID/Department information =>
    it's impossible to accurately link them to Teacher model.
    """

    short_name: str
    full_name: str



class TeacherInfo(Schema):
    uuid: pydantic.UUID4

    short_name: str
    full_name: str

    departments: list[pydantic.UUID4]


class Subscription(Schema):
    is_active: bool

    groups: list[Group]
    teachers: list[Teacher]



class Lesson(Schema):
    short_name: str = pydantic.Field(examples=["ПНМ (Онлайн лек.)"])
    full_name: str = pydantic.Field(examples=["Професійно-наукова мова"])

    teacher: TeacherInfo | ScheduleTeacherInfo

    card: str | None = pydantic.Field(
        default=None,
        examples=[
            "Ідентифікатор конференції: XXX YYY ZZZ\r\nКод доступу: ABCDEFG",  # noqa: RUF001
        ],
    )
    auditorium: str | None = pydantic.Field(
        default=None,
        examples=["B-123", "Онлайн"],
    )


class Pair(Schema):
    number: int = pydantic.Field(
        ge=1,
    )

    lessons: list[Lesson]


class DaySchedule(Schema):
    date: datetime.date

    pairs: list[Pair]


class WeekSchedule(Schema):
    days: list[DaySchedule]
