from sqlalchemy.orm import Session

from core.access import AccessContext
from core.exceptions import PermissionDenied
from db.minio_client import BUCKET_NAMES
from profile.dtos.dashboard_dto import DashboardPayload, StudentTaskPayload
from profile.policies.dashboard_policy import DashboardPolicy
from profile.repositories.dashboard_repository import dashboard_repository
from infrastructure.storage.file_service import file_service
from models.domains.student import RatingsHistory, StudentProfile, StudentTask, Task, TaskMedia
from models.domains.auth import User
from models.domains.education import Group, GroupEnrollment


class DashboardService:
    def get_dashboard_payload(self, db: Session, *, ctx: AccessContext):
        try:
            DashboardPolicy.require_view_own_dashboard(ctx)
        except PermissionDenied as exc:
            raise PermissionDenied("Access denied to dashboard") from exc

        user_id = ctx.user_id
        profile = dashboard_repository.get_profile(db, user_id=user_id)
        user = dashboard_repository.get_user(db, user_id=user_id)
        tasks = dashboard_repository.get_tasks(db, user_id=user_id)
        videos = dashboard_repository.get_videos(db, user_id=user_id)

        user_achievements = dashboard_repository.get_user_achievements(db, user_id=user_id, limit=50)

        individual_achievements = []
        collective_awarded_at = {}

        for ua in user_achievements:
            achievement = ua.achievement
            if not achievement:
                continue
            if achievement.is_collective:
                collective_awarded_at[achievement.id] = ua.awarded_at.isoformat() if ua.awarded_at else None
                continue

            individual_achievements.append({
                "id": achievement.id,
                "title": achievement.title,
                "description": achievement.description,
                "event_date": achievement.event_date.isoformat() if achievement.event_date else None,
                "place": achievement.place,
                "is_collective": False,
                "file_url": file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"]) if achievement.certificate_url else None,
                "video_url": file_service.get_file_url(achievement.video_url, BUCKET_NAMES["achievement_videos"]) if achievement.video_url and achievement.is_public else None,
                "awarded_at": ua.awarded_at.isoformat() if ua.awarded_at else None,
            })

        collective_achievements = dashboard_repository.get_collective_achievements(db, limit=50)
        collective_achievements_result = []

        for achievement in collective_achievements:
            collective_achievements_result.append({
                "id": achievement.id,
                "title": achievement.title,
                "description": achievement.description,
                "event_date": achievement.event_date.isoformat() if achievement.event_date else None,
                "place": achievement.place,
                "is_collective": True,
                "file_url": file_service.get_file_url(achievement.certificate_url, BUCKET_NAMES["certificates"]) if achievement.certificate_url else None,
                "video_url": file_service.get_file_url(achievement.video_url, BUCKET_NAMES["achievement_videos"]) if achievement.video_url and achievement.is_public else None,
                "awarded_at": collective_awarded_at.get(achievement.id),
            })

        achievement_videos = [
            {
                "id": achievement["id"],
                "title": achievement["title"],
                "description": achievement["description"],
                "event_date": achievement["event_date"],
                "place": achievement["place"],
                "file_url": achievement["file_url"],
                "video_url": achievement["video_url"],
                "awarded_at": achievement["awarded_at"],
            }
            for achievement in individual_achievements
            if achievement.get("video_url")
        ] + [
            {
                "id": achievement["id"],
                "title": achievement["title"],
                "description": achievement["description"],
                "event_date": achievement["event_date"],
                "place": achievement["place"],
                "is_collective": achievement["is_collective"],
                "file_url": achievement["file_url"],
                "video_url": achievement["video_url"],
                "awarded_at": achievement["awarded_at"],
            }
            for achievement in collective_achievements_result
            if achievement.get("video_url")
        ]

        ranking_enrollment = (
            db.query(GroupEnrollment)
            .filter(
                GroupEnrollment.student_id == user_id,
                GroupEnrollment.status == "active",
            )
            .order_by(GroupEnrollment.id)
            .first()
        )
        ranking_group = ranking_enrollment.group if ranking_enrollment else None
        ranking_members = (
            db.query(GroupEnrollment)
            .filter(
                GroupEnrollment.group_id == ranking_group.id,
                GroupEnrollment.status == "active",
            )
            .all()
            if ranking_group else []
        )
        ranking_scores = sorted(
            [
                {
                    "user_id": member.student_id,
                    "rating": sum(task.grade or 0 for task in member.tasks),
                }
                for member in ranking_members
            ],
            key=lambda item: (-item["rating"], item["user_id"]),
        )
        eligible_enrollments = (
            db.query(GroupEnrollment)
            .join(Group)
            .filter(
                GroupEnrollment.status == "active",
                Group.status == "active",
                Group.leaderboard_enabled.is_(True),
            )
            .all()
        )
        overall_scores_by_user = {}
        for enrollment in eligible_enrollments:
            overall_scores_by_user[enrollment.student_id] = overall_scores_by_user.get(enrollment.student_id, 0) + sum(
                task.grade or 0 for task in enrollment.tasks
            )
        overall_ranking_scores = sorted(
            [
                {"user_id": student_id, "rating": rating}
                for student_id, rating in overall_scores_by_user.items()
            ],
            key=lambda item: (-item["rating"], item["user_id"]),
        )
        user_rating = next(
            (item["rating"] for item in ranking_scores if item["user_id"] == user_id),
            0,
        ) if ranking_group else (profile.rating_points if profile else 0)
        higher_rank_count = sum(item["rating"] > user_rating for item in ranking_scores) if ranking_group else db.query(StudentProfile).filter(StudentProfile.rating_points > user_rating).count()
        total_students = len(ranking_members) if ranking_group else db.query(StudentProfile).count()
        user_place = higher_rank_count + 1 if profile else None

        history_records = dashboard_repository.get_history(db, user_id=user_id, limit=20)

        history = []
        current_points = user_rating
        for record in history_records:
            history.append({
                "timestamp": record.created_at.isoformat() if record.created_at else None,
                "points_change": record.points_change,
                "reason": record.reason,
                "points_after": current_points,
                "direction": "up" if record.points_change > 0 else "down" if record.points_change < 0 else "same",
                "place_estimate": sum(item["rating"] > current_points for item in ranking_scores) + 1 if ranking_group else db.query(StudentProfile.rating_points).filter(StudentProfile.rating_points > current_points).distinct().count() + 1,
            })
            current_points -= record.points_change
        history.reverse()

        leaderboard = []

        if ranking_group:
            leaderboard_entries = ranking_scores[:10]
            if not any(item["user_id"] == user_id for item in leaderboard_entries):
                leaderboard_entries.append(next(item for item in ranking_scores if item["user_id"] == user_id))
        else:
            leaderboard_profiles = dashboard_repository.get_leaderboard_profiles(db, limit=10)
            if profile and all(item.user_id != user_id for item in leaderboard_profiles):
                leaderboard_profiles.append(profile)
            leaderboard_entries = [
                {"user_id": item.user_id, "rating": item.rating_points, "profile": item}
                for item in leaderboard_profiles
            ]

        ranking_users = {
            item.id: item
            for item in db.query(User).filter(
                User.id.in_([item["user_id"] for item in leaderboard_entries]),
            ).all()
        } if ranking_group else {}

        for leaderboard_entry in leaderboard_entries:
            profile_item = leaderboard_entry.get("profile")
            item_rating = leaderboard_entry["rating"]
            item_place = sum(item["rating"] > item_rating for item in ranking_scores) + 1 if ranking_group else db.query(StudentProfile).filter(StudentProfile.rating_points > item_rating).count() + 1

            last_history = (
                db.query(RatingsHistory)
                .filter(RatingsHistory.student_id == leaderboard_entry["user_id"])
                .order_by(RatingsHistory.created_at.desc())
                .first()
            )

            movement = "same"
            if last_history:
                if last_history.points_change > 0:
                    movement = "up"
                elif last_history.points_change < 0:
                    movement = "down"

            leaderboard.append({
                "place": item_place,
                "user_id": leaderboard_entry["user_id"],
                "full_name": (
                    f"{profile_item.user.first_name} {profile_item.user.last_name}".strip()
                    if profile_item else f"{ranking_users[leaderboard_entry['user_id']].first_name} {ranking_users[leaderboard_entry['user_id']].last_name or ''}".strip()
                ),
                "rating": item_rating,
                "movement": movement,
                "group_id": ranking_group.id if ranking_group else None,
                "group_title": ranking_group.title if ranking_group else None,
            })

        overall_user_entry = next(
            (item for item in overall_ranking_scores if item["user_id"] == user_id),
            None,
        )
        overall_leaderboard = []
        overall_entries = overall_ranking_scores
        if overall_user_entry and not any(item["user_id"] == user_id for item in overall_entries):
            overall_entries.append(overall_user_entry)
        overall_users = {
            item.id: item
            for item in db.query(User).filter(
                User.id.in_([item["user_id"] for item in overall_entries]),
            ).all()
        } if overall_entries else {}
        for entry in overall_entries:
            user_record = overall_users.get(entry["user_id"])
            if not user_record:
                continue
            last_history = (
                db.query(RatingsHistory)
                .filter(RatingsHistory.student_id == entry["user_id"])
                .order_by(RatingsHistory.created_at.desc())
                .first()
            )
            overall_leaderboard.append({
                "place": sum(item["rating"] > entry["rating"] for item in overall_ranking_scores) + 1,
                "user_id": entry["user_id"],
                "full_name": f"{user_record.first_name} {user_record.last_name or ''}".strip(),
                "rating": entry["rating"],
                "movement": "up" if last_history and last_history.points_change > 0 else "down" if last_history and last_history.points_change < 0 else "same",
                "group_id": None,
                "group_title": "ALANKO",
            })

        student_group_enrollments = (
            db.query(GroupEnrollment)
            .join(Group)
            .filter(
                GroupEnrollment.student_id == user_id,
                GroupEnrollment.status == "active",
                Group.status == "active",
            )
            .order_by(GroupEnrollment.id)
            .all()
        )
        group_leaderboards = []
        processed_group_ids = set()
        for student_enrollment in student_group_enrollments:
            group = student_enrollment.group
            if group.id in processed_group_ids:
                continue
            processed_group_ids.add(group.id)
            group_members = (
                db.query(GroupEnrollment)
                .filter(
                    GroupEnrollment.group_id == group.id,
                    GroupEnrollment.status == "active",
                )
                .all()
            )
            group_scores = sorted(
                [
                    {
                        "user_id": member.student_id,
                        "rating": sum(task.grade or 0 for task in member.tasks),
                    }
                    for member in group_members
                ],
                key=lambda item: (-item["rating"], item["user_id"]),
            )
            group_users = {
                item.id: item
                for item in db.query(User).filter(
                    User.id.in_([item["user_id"] for item in group_scores]),
                ).all()
            } if group_scores else {}
            group_entries = []
            for entry in group_scores:
                group_user = group_users.get(entry["user_id"])
                if not group_user:
                    continue
                group_entries.append({
                    "place": sum(item["rating"] > entry["rating"] for item in group_scores) + 1,
                    "user_id": entry["user_id"],
                    "full_name": f"{group_user.first_name} {group_user.last_name or ''}".strip(),
                    "rating": entry["rating"],
                    "group_id": group.id,
                    "group_title": group.title,
                })
            group_leaderboards.append({
                "group_id": group.id,
                "group_title": group.title,
                "entries": group_entries,
                "total_students": len(group_scores),
            })

        return DashboardPayload(
            user_id=user_id,
            rating=profile.rating_points if profile else 0,
            tasks=len(tasks),
            place=user_place,
            total_students=total_students,
            history=history,
            leaderboard=leaderboard,
            leaderboards={"group": leaderboard, "groups": group_leaderboards, "overall": overall_leaderboard},
            leaderboard_totals={
                "group": len(ranking_scores),
                "overall": len(overall_ranking_scores),
            },
            videos=[{"id": v.id, "url": file_service.get_file_url(v.video_url, BUCKET_NAMES["videos"])} for v in videos],
            achievement_videos=achievement_videos,
            achievements={"individual": individual_achievements, "collective": collective_achievements_result},
            user={
                "full_name": " ".join(part for part in (user.first_name, user.middle_name, user.last_name) if part).strip() if user else None,
                "email": user.email if user else None,
                "image_url": file_service.get_file_url(
                    user.image_url or (profile.image_url if profile else None),
                    BUCKET_NAMES["student_photos"],
                ) if (user and (user.image_url or (profile and profile.image_url))) else None,
            },
        ).to_dict()

    def get_student_tasks_payload(self, db: Session, *, ctx: AccessContext):
        try:
            DashboardPolicy.require_view_own_tasks(ctx)
        except PermissionDenied as exc:
            raise PermissionDenied("Access denied to student tasks") from exc

        student_tasks = dashboard_repository.get_student_tasks(db, user_id=ctx.user_id)

        return [
            StudentTaskPayload(
                student_task_id=st.id,
                task_id=st.task.id if st.task else None,
                title=st.task.title if st.task else None,
                description=st.task.description if st.task else None,
                category_name=st.task.category.name if st.task and st.task.category else None,
                status=st.status,
                score=st.score,
                max_score=st.task.max_score if st.task else None,
                has_video=len(st.media) > 0,
                videos=[{
                    "media_id": media.id,
                    "video_url": file_service.get_file_url(media.video_url, BUCKET_NAMES["videos"]),
                    "download_url": file_service.get_file_url(media.video_url, BUCKET_NAMES["videos"]),
                } for media in st.media[:20]],
            ).to_dict()
            for st in student_tasks
        ]

    def get_student_program_progress_payload(self, db: Session, *, ctx: AccessContext):
        try:
            DashboardPolicy.require_view_own_tasks(ctx)
        except PermissionDenied as exc:
            raise PermissionDenied("Access denied to program progress") from exc

        enrollments = (
            db.query(GroupEnrollment)
            .filter(
                GroupEnrollment.student_id == ctx.user_id,
                GroupEnrollment.status == "active",
            )
            .all()
        )
        group_enrollments = (
            db.query(GroupEnrollment)
            .filter(GroupEnrollment.status == "active")
            .all()
        )
        group_members = {}
        for group_enrollment in group_enrollments:
            member_points = sum(task.grade or 0 for task in group_enrollment.tasks)
            member_completed = sum(
                1 for task in group_enrollment.tasks
                if task.status == "completed" or task.grade is not None
            )
            group_members.setdefault(group_enrollment.group_id, []).append({
                "student_id": group_enrollment.student_id,
                "points": member_points,
                "completed_tasks": member_completed,
            })

        result = []
        for enrollment in enrollments:
            group = enrollment.group
            program = group.program if group else None
            if not group or not program:
                continue

            progress_by_task_id = {task.program_task_id: task for task in enrollment.tasks}
            members = sorted(
                group_members.get(group.id, []),
                key=lambda member: (-member["points"], member["student_id"]),
            )
            student_group_points = next(
                (member["points"] for member in members if member["student_id"] == ctx.user_id),
                0,
            )
            student_group_completed = next(
                (member["completed_tasks"] for member in members if member["student_id"] == ctx.user_id),
                0,
            )
            student_group_place = next(
                (index + 1 for index, member in enumerate(members) if member["student_id"] == ctx.user_id),
                None,
            )
            blocks = []
            for block in program.blocks:
                program_tasks = [task for topic in block.topics for task in topic.tasks]
                completed_tasks = 0
                task_payloads = []
                for program_task in program_tasks:
                    student_task = progress_by_task_id.get(program_task.id)
                    group_task_media = (
                        db.query(TaskMedia)
                        .filter(TaskMedia.group_student_task_id == student_task.id)
                        .order_by(TaskMedia.created_at.desc(), TaskMedia.id.desc())
                        .all()
                        if student_task else []
                    )
                    is_completed = bool(
                        student_task
                        and (student_task.status == "completed" or student_task.grade is not None)
                    )
                    completed_tasks += int(is_completed)
                    task_payloads.append({
                        "student_task_id": student_task.id if student_task else None,
                        "program_task_id": program_task.id,
                        "title": program_task.title,
                        "description": program_task.description,
                        "status": student_task.status if student_task else "not_started",
                        "grade": student_task.grade if student_task else None,
                        "feedback": student_task.feedback if student_task else None,
                        "max_score": program_task.max_score,
                        "videos": [{
                            "media_id": media.id,
                            "video_url": file_service.get_file_url(media.video_url, BUCKET_NAMES["videos"]),
                            "download_url": file_service.get_file_url(media.video_url, BUCKET_NAMES["videos"]),
                        } for media in group_task_media],
                    })

                total_tasks = len(program_tasks)
                blocks.append({
                    "id": block.id,
                    "title": block.title,
                    "description": block.description,
                    "order": block.order,
                    "completed_tasks": completed_tasks,
                    "total_tasks": total_tasks,
                    "completion_percent": round(completed_tasks * 100 / total_tasks) if total_tasks else 0,
                    "tasks": task_payloads,
                })

            result.append({
                "group_id": group.id,
                "group_title": group.title,
                "program": {"id": program.id, "title": program.title},
                "group_rating": {
                    "points": student_group_points,
                    "place": student_group_place,
                    "total_students": len(members),
                    "completed_tasks": student_group_completed,
                },
                "blocks": blocks,
            })
        return result


dashboard_service = DashboardService()
