class EducationError(Exception):
    """Base exception for education domain errors."""


class PermissionDenied(EducationError):
    pass


class ProgramNotFound(EducationError):
    pass


class BlockNotFound(EducationError):
    pass


class TaskNotFound(EducationError):
    pass


class EnrollmentNotFound(EducationError):
    pass


class ProgramTaskNotFound(EducationError):
    pass


class StudentTaskNotFound(EducationError):
    pass


class StudentNotFound(EducationError):
    pass


class InvalidStudentTaskScore(EducationError):
    pass


class CategoryAlreadyExists(EducationError):
    pass


class CategoryNotFound(EducationError):
    pass


class NoStudentsFound(EducationError):
    pass
