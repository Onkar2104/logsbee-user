from pydantic import BaseModel, EmailStr, Field, SecretStr, model_validator


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(pattern=r"^[0-9]{6}$")
    new_password: SecretStr
    confirm_password: SecretStr

    @model_validator(mode="after")
    def check_passwords_match(self):
        if (
            self.new_password.get_secret_value()
            != self.confirm_password.get_secret_value()
        ):
            raise ValueError("Passwords do not match.")

        return self