from pydantic import BaseModel


class PronounceCantoneseRequest(BaseModel):
    text: str
