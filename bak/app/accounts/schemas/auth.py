from pydantic import BaseModel, EmailStr


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class AdminAddUserSchema(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str | None = None
    middle_name: str
    role: str
    birth_year: int | None = None


class TeacherAddStudentSchema(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str | None = None
    middle_name: str
    birth_year: int | None = None


class StudentUpdateSchema(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    birth_year: int | None = None
