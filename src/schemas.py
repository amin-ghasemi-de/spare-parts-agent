from typing import Literal

from pydantic import BaseModel, Field


class RequestedItem(BaseModel):
    part_no: str | None = Field(
        default=None,
        description="Part number exactly as written in the e-mail, or null if none is given.",
    )
    description: str = Field(
        description="Name or description of the part as written in the e-mail.",
    )
    quantity: int | None = Field(
        default=None,
        ge=1,
        description="Requested quantity, or null if not stated.",
    )


class SparePartRequest(BaseModel):
    is_spare_part_request: bool = Field(
        description="True if the e-mail asks for spare parts, otherwise false.",
    )
    customer_company: str | None = Field(default=None, description="Company name of the sender.")
    contact_name: str | None = Field(default=None, description="Name of the person who wrote the e-mail.")
    contact_email: str | None = Field(default=None, description="E-mail address of the sender.")
    machine_model: str | None = Field(
        default=None,
        description="Machine model the parts are for, e.g. HPC-300.",
    )
    urgency: Literal["low", "normal", "high"] = Field(
        default="normal",
        description="high = machine down, urgent or asap; low = customer says it is not urgent; otherwise normal.",
    )
    language: Literal["de", "en", "mixed"] = Field(
        description="Main language of the e-mail.",
    )
    items: list[RequestedItem] = Field(
        default_factory=list,
        description="One entry per requested part.",
    ) 