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
    role: str  # "student", "teacher", "admin"


class TeacherAddStudentSchema(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str | None = None
    middle_name: str