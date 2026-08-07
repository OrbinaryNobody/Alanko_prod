import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from achievements.policies.achievement_policy import AchievementPolicy
from assessment.policies.assessment_policy import AssessmentPolicy
from core.access import AccessContext
from media.policies.media_policy import MediaPolicy


def test_achievement_policy_allows_manage_permission():
    ctx = AccessContext.from_parts(user_id=1, roles=["teacher"], permissions=["manage_achievements"], is_admin=False)
    AchievementPolicy.require_manage_achievements(ctx)


def test_assessment_policy_allows_view_permission():
    ctx = AccessContext.from_parts(user_id=2, roles=["student"], permissions=["view_assessment"], is_admin=False)
    AssessmentPolicy.require_view_assessment(ctx)


def test_media_policy_allows_upload_permission():
    ctx = AccessContext.from_parts(user_id=3, roles=["teacher"], permissions=["upload_media"], is_admin=False)
    MediaPolicy.require_upload_media(ctx)
