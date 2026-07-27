from pydantic import BaseModel


class ProgramCreate(BaseModel):
    title: str
    description: str | None = None


class ProgramBlockCreate(BaseModel):
    title: str
    description: str | None = None
    order: int = 0


class ProgramTaskCreate(BaseModel):
    title: str
    description: str | None = None
    max_score: int = 100
    is_manual: bool = False


class GroupCreate(BaseModel):
    title: str
    description: str | None = None
    program_id: int | None = None


class GroupMemberCreate(BaseModel):
    user_id: int
    role: str = "teacher"


class EnrollmentCreate(BaseModel):
    student_id: int


class ManualTaskCreate(BaseModel):
    enrollment_id: int
    program_task_id: int


class GradeUpdate(BaseModel):
    grade: int
    feedback: str | None = None
