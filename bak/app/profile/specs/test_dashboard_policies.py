import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from core.access import AccessContext
from profile.policies.dashboard_policy import DashboardPolicy


def test_dashboard_policy_allows_admin_and_permissioned_user():
    admin_ctx = AccessContext.from_parts(user_id=1, roles=["admin"], permissions=[], is_admin=True)
    allowed_ctx = AccessContext.from_parts(user_id=2, roles=["student"], permissions=["view_own_dashboard", "view_own_tasks"], is_admin=False)

    DashboardPolicy.require_view_own_dashboard(admin_ctx)
    DashboardPolicy.require_view_own_dashboard(allowed_ctx)
    DashboardPolicy.require_view_own_tasks(allowed_ctx)


def test_dashboard_policy_denies_user_without_permission():
    ctx = AccessContext.from_parts(user_id=3, roles=["student"], permissions=[], is_admin=False)

    try:
        DashboardPolicy.require_view_own_dashboard(ctx)
    except PermissionError:
        pass
    else:
        raise AssertionError("Expected PermissionError")
