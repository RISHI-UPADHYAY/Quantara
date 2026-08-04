from pydantic import BaseModel

class VerifyEmailResponse(BaseModel):
    token: str