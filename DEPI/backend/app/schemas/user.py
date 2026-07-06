from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    age: int | None = Field(default=None, ge=0, le=130)
    gender: str | None = Field(default=None, max_length=50)
    activity_level: str | None = Field(default=None, max_length=50)
    allergies: str | None = Field(default=None, max_length=500)
    conditions: str | None = Field(default=None, max_length=500)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(min_length=20)


class UserOut(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
