
from pydantic import BaseModel, Field


class OTPVerifyRequest(BaseModel):
    otp: str = Field(pattern=r"^[0-9]{6}$")

class OTPRequest(BaseModel):
    otp: str | None = Field(
        default=None,
        pattern=r"^[0-9]{6}$"
    )

class VerificationResponse(BaseModel):
    message: str
