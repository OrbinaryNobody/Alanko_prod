import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from core.permissions import Permission
from schedule.api import routes as calendar_routes


def test_calendar_permissions_include_group_access():
    required = calendar_routes.CALENDAR_ACCESS_PERMISSIONS
    assert Permission.VIEW_GROUPS in required
    assert Permission.MANAGE_GROUPS in required
    assert Permission.VIEW_CONSULTATIONS in required
    assert Permission.MANAGE_CONSULTATIONS in required
