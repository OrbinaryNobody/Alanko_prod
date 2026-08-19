from core.access import AccessContext
from consultations.models.consultation_slot import ConsultationSlot


class ConsultationPolicy:
    @staticmethod
    def require_manage_slot(ctx: AccessContext, slot: ConsultationSlot) -> None:
        if ctx.is_admin or slot.teacher_id == ctx.user_id or slot.created_by == ctx.user_id:
            return
        raise PermissionError("Access denied to manage consultation slot")


consultation_policy = ConsultationPolicy()
