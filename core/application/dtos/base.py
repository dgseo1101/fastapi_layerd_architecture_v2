# -*- coding: utf-8 -*-
from abc import ABC

from pydantic import BaseModel, ConfigDict

dto_model_config = ConfigDict(
    extra="ignore",
    frozen=True,
    populate_by_name=True,
    loc_by_alias=True,
    ser_json_timedelta="iso8601",
    ser_json_bytes="utf8",
)


class BaseRequest(ABC, BaseModel):
    model_config = dto_model_config


class BaseResponse(ABC, BaseModel):
    model_config = dto_model_config
