from datetime import date, time

from pydantic import BaseModel, Field, model_validator


class ProgramCreate(BaseModel):
    title: str
    description: str | None = None


class ProgramTaskProposal(BaseModel):
    id: int | None = None
    title: str
    description: str | None = None
    max_score: int = Field(ge=0, le=100000)
    order: int = 0
    is_manual: bool = False


class ProgramTopicProposal(BaseModel):
    id: int | None = None
    title: str
    description: str | None = None
    order: int = 0
    tasks: list[ProgramTaskProposal] = Field(default_factory=list)


class ProgramBlockProposal(BaseModel):
    id: int | None = None
    title: str
    description: str | None = None
    order: int = 0
    topics: list[ProgramTopicProposal] = Field(default_factory=list)


class ProgramChangeProposalCreate(BaseModel):
    title: str | None = None
    description: str | None = None
    blocks: list[ProgramBlockProposal]
    comment: str | None = None


class ProgramChangeDecision(BaseModel):
    comment: str | None = None


class ProgramBlockCreate(BaseModel):
    title: str
    description: str | None = None
    order: int = 0


class ProgramTopicCreate(BaseModel):
    title: str
    description: str | None = None
    order: int = 0


class ProgramTaskCreate(BaseModel):
    title: str
    description: str | None = None
    max_score: int = 100
    is_manual: bool = False


class ProgramBlockUpdate(BaseModel):
    title: str
    description: str | None = None
    order: int = 0


class ProgramTopicUpdate(BaseModel):
    title: str
    description: str | None = None
    order: int = 0


class ProgramTaskUpdate(BaseModel):
    title: str
    description: str | None = None
    max_score: int = Field(ge=0, le=100000)
    is_manual: bool = False
    order: int = 0


class GroupCreate(BaseModel):
    title: str
    description: str | None = None
    program_id: int | None = None


class GroupUpdate(BaseModel):
    title: str
    description: str | None = None
    leaderboard_enabled: bool = False


class GroupTaskGradeUpdate(BaseModel):
    grade: int = Field(ge=0, le=100000)
    feedback: str | None = None


class GroupMemberCreate(BaseModel):
    user_id: int
    role: str = "teacher"


class GroupTeacherCreate(BaseModel):
    user_id: int


class GroupStudentCreate(BaseModel):
    student_id: int


class EnrollmentCreate(BaseModel):
    student_id: int


class GroupScheduleCreate(BaseModel):
    teacher_id: int
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    valid_from: date
    valid_until: date | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until must not be before valid_from")
        return self


class ManualTaskCreate(BaseModel):
    enrollment_id: int
    program_task_id: int


class GradeUpdate(BaseModel):
    grade: int
    feedback: str | None = None
