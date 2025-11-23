import datetime
from typing import Literal, TypeVar
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

    def as_string(self) -> str:
        return f"{self.short_name} ({self.faculty.short_name})"


class Department(Schema):
    uuid: pydantic.UUID4

    short_name: str
    full_name: str


class Teacher(Schema):
    uuid: pydantic.UUID4

    short_name: str
    full_name: str

    departments: list[Department]

    def as_string(self) -> str:
        return f"{self.full_name}"


class ScheduleTeacherInfo(Schema):
    """
    This class is used in places that can only get
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

    def _as_string_short(self) -> str:
        return f"{self.short_name} - {self.teacher.full_name}"

    def _as_string_full(self) -> str:
        parts = [f"{self.short_name} - {self.full_name}"]

        parts.append(f"Викладач: {self.teacher.full_name}")

        if self.auditorium:
            parts.append(f"Аудиторія: {self.auditorium}")

        if self.card:
            parts.append(f"Деталі: {self.card}")

        return "\n".join(parts)

    def as_string(self, format: Literal["short", "full"] = "short") -> str:
        if format == "short":
            return self._as_string_short()
        else:
            return self._as_string_full()


class Pair(Schema):
    number: int = pydantic.Field(
        ge=1,
    )

    lessons: list[Lesson]


class DaySchedule(Schema):
    for_entity: str

    date: datetime.date

    pairs: list[Pair]


class WeekSchedule(Schema):
    for_entity: str

    days: list[DaySchedule]


T = TypeVar("T", bound=Schema)


class PageNumberPaginationInput(Schema):
    page: int = pydantic.Field(1, ge=1)
    page_size: int | None = pydantic.Field(None, ge=1)


class PaginatedRequest(PageNumberPaginationInput):
    pass


class Meta(Schema):
    total: int
    page: int
    page_size: int

    has_next: bool = False
    has_previous: bool = False

    @property
    def total_pages(self) -> int:
        if self.page_size is None or self.page_size == 0:
            return 1

        return (self.total + self.page_size - 1) // self.page_size


class PaginatedResponse[T](Schema):
    meta: Meta
    items: list[T]


class FacultyPaginatedRequest(PaginatedRequest):
    name: str | None = pydantic.Field(
        default=None,
        description="Filter faculties by name (partial match).",
    )


class FacultyPaginatedResponse(PaginatedResponse[Faculty]):
    pass


class GroupPaginatedRequest(PaginatedRequest):
    faculty_id: pydantic.UUID4 | None = pydantic.Field(
        default=None,
        description="Filter groups by faculty ID.",
    )
    name: str | None = pydantic.Field(
        default=None,
        description="Filter groups by name (partial match).",
    )


class GroupPaginatedResponse(PaginatedResponse[Group]):
    pass


class DepartmentPaginatedRequest(PaginatedRequest):
    name: str | None = pydantic.Field(
        default=None,
        description="Filter departments by name (partial match).",
    )


class DepartmentPaginatedResponse(PaginatedResponse[Department]):
    pass


class TeacherPaginatedRequest(PaginatedRequest):
    department_id: pydantic.UUID4 | None = pydantic.Field(
        default=None,
        description="Filter teachers by department ID.",
    )

    name: str | None = pydantic.Field(
        default=None,
        description="Filter teachers by name (partial match).",
    )


class TeacherPaginatedResponse(PaginatedResponse[Teacher]):
    pass
