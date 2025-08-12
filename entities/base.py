from typing import Dict

from pydantic import BaseModel


class BaseResponse(BaseModel):
    code: int
    message: str
    data: Dict


def new_success_response(data=None):
    if not data:
        data = {}
    return BaseResponse(
        code=0,
        message="success",
        data=data
    )
