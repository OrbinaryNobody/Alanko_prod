import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from consultations.api.admin import resolve_consultation_teacher_id
from consultations.services.slot_service import SlotService
from core.permissions import require_student_consultation_booking
from shared.access.access_context import AccessContext


def test_admin_created_consultation_defaults_to_current_admin_user():
    ctx = AccessContext.from_parts(user_id=42, roles=["admin"], permissions=[], is_admin=True)

    assert resolve_consultation_teacher_id(ctx, teacher_id=8) == 42


def test_teacher_created_consultation_keeps_teacher_identity():
    ctx = AccessContext.from_parts(user_id=9, roles=["teacher"], permissions=[], is_admin=False)

    assert resolve_consultation_teacher_id(ctx, teacher_id=9) == 9


def test_private_slot_overlaps_are_detected():
    start_a = datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc)
    end_a = datetime(2026, 9, 1, 19, 0, tzinfo=timezone.utc)
    start_b = datetime(2026, 9, 1, 18, 30, tzinfo=timezone.utc)
    end_b = datetime(2026, 9, 1, 19, 30, tzinfo=timezone.utc)

    assert SlotService._slots_overlap(start_a, end_a, start_b, end_b)


def test_only_students_can_book_consultations():
    dependency = require_student_consultation_booking()
    student = AccessContext.from_parts(user_id=1, roles=["student"], permissions=[])
    staff = AccessContext.from_parts(user_id=2, roles=["admin"], permissions=[], is_admin=True)

    assert dependency(student) is student

    try:
        dependency(staff)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
    else:
        raise AssertionError("Staff users must not book consultations")
