import httpx


class EntityNotFoundError(Exception):
    """Base class for not found errors."""

    def __init__(self, response: "httpx.Response") -> None:
        self.response = response
        self.request = response.request

        message = self.make_message()

        super().__init__(message)

    def make_message(self) -> str:
        return f"Entity not found for request: {self.request.method} {self.request.url}"


class SubscriptionNotFoundError(EntityNotFoundError):
    """Raised when a subscription is not found."""

    def __init__(self, response: httpx.Response, chat_id: str) -> None:
        self.chat_id = chat_id
        super().__init__(response)

    def make_message(self) -> str:
        return (
            f"Subscription not found for {self.chat_id=} in request: "
            f"{self.request.method} {self.request.url}"
        )
