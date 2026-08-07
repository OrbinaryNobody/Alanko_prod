from sqlalchemy.orm import Session

from core.access import AccessContext
from profile.services.dashboard_service import dashboard_service


class ProfileFacade:
    def get_dashboard_payload(self, db: Session, *, ctx: AccessContext):
        return dashboard_service.get_dashboard_payload(db, ctx=ctx)

    def get_student_tasks_payload(self, db: Session, *, ctx: AccessContext):
        return dashboard_service.get_student_tasks_payload(db, ctx=ctx)


profile_facade = ProfileFacade()
