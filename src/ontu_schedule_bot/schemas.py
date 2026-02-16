import pydantic

from ontu_schedule_bot.third_party.admin.schemas import Chat


class SendMessageCampaignDTO(pydantic.BaseModel):
    name: str
    payload: dict
    recipients: list[Chat]
