from sqlalchemy.orm import Session

from core.access import AccessContext
from assessment.services.assessment_service import assessment_service


class AssessmentFacade:
    def get_assessment_payload(self, db: Session, *, ctx: AccessContext, student_id: int, task_id: int):
        return assessment_service.get_assessment_payload(db, ctx=ctx, student_id=student_id, task_id=task_id)


assessment_facade = AssessmentFacade()
